import os
import json
import re
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QCoreApplication
from Python.ui.name_utils import normalize_name_for_matching
from Python.ui.steam_cache import STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE # Only import constants, not functions
from Python import constants
from datetime import datetime

# Import custom events from main_window_new
from Python.main_window_new import _StatusUpdateEvent, _EnableUIEvent

class SteamProcessor:
    def __init__(self, main_window, steam_cache_manager):
        self.main_window = main_window
        self.steam_cache_manager = steam_cache_manager

    def _log_and_status(self, message: str, timeout: int = 0, append_log: bool = True):
        """Post a status update to the UI and optionally append to the app log.

        This centralises logging so both the status bar and app.log contain
        the same informative messages during long-running streaming parse.
        """
        try:
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(message, timeout))
        except Exception:
            # If posting the event fails, continue - we still want to write the log
            pass

        if append_log:
            try:
                ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                with open(constants.APP_LOG_FILE, 'a', encoding='utf-8') as logf:
                    logf.write(f"{ts} - {message}\n")
            except Exception:
                # Don't let logging failures stop processing
                pass

    def prompt_and_process_steam_json(self):
        """Prompt user to select and process Steam JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, "Select Steam JSON file", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self.start_processing(file_path)

    def start_processing(self, file_path):
        """Start processing a Steam JSON file in a background thread"""
        if not file_path:
            return

        # Backup existing cache files before processing using the SteamCacheManager
        self.steam_cache_manager.backup_cache_files()

        # Disable UI elements
        self._disable_ui_elements()
        QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("Please be patient as the steam.json file is cached...", 0))

        # Process the file in a separate thread to show progress
        import threading
        process_thread = threading.Thread(target=self._process_with_progress, args=(file_path,))
        process_thread.daemon = True
        process_thread.start()

    def _process_with_progress(self, file_path):
        """Process Steam JSON file with progress updates."""
        try:
            # Update status with processing start
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("Processing Steam JSON file...", 0))

            # Process the file
            success = self.process_steam_json_file(file_path)

            # Update status bar based on result
            if success:
                QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("Steam.json file indexing complete.", 5000))
            else:
                QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("Steam.json file indexing failed.", 5000))

        except Exception as e:
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Error processing Steam JSON: {str(e)}", 5000))
        finally:
            # Re-enable UI elements
            QCoreApplication.postEvent(self.main_window, _EnableUIEvent())

    def process_steam_json_file(self, input_json_path: str):
        """Process a Steam JSON file to extract title data"""
        if not os.path.exists(input_json_path):
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Steam JSON file not found: {input_json_path}", 5000))
            return False
        
        try:
            # Process the file
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Processing Steam JSON: {input_json_path}", 0))
            
            # Store the path for later reference
            self.main_window.steam_json_file_path = input_json_path
            
            # Load the JSON data. Try a full load first, but if the file is very
            # large we fall back to a streaming/object-extraction parser that
            # doesn't require loading the entire file into memory.
            data = None
            try:
                with open(input_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._log_and_status("steam_processor: full json.load() succeeded", 0)
            except MemoryError:
                # Will fall back to streaming parser below
                data = None
                self._log_and_status("steam_processor: json.load() raised MemoryError; will use streaming fallback", 0)
            except json.JSONDecodeError:
                # Bad format for full-load; we'll also try streaming fallback
                data = None
                self._log_and_status("steam_processor: json.load() raised JSONDecodeError; will use streaming fallback", 0)
                
            # Filter and extract title data
            local_title_cache = {}

            # apps_list will be filled either from the fully-loaded JSON above
            # or via a streaming fallback parser below.
            apps_list = []

            if isinstance(data, dict):
                # Check for common Steam JSON container structures
                if 'applist' in data and isinstance(data['applist'], dict) and 'apps' in data['applist']:
                    apps_list = data['applist']['apps']
                elif 'response' in data and isinstance(data['response'], dict) and 'apps' in data['response']:
                    apps_list = data['response']['apps']
                else:
                    apps_list = data.get('apps', [])
            elif isinstance(data, list):
                apps_list = data

            # If we couldn't load the file into memory or didn't find apps,
            # try a streaming extraction that looks for JSON objects inside an
            # "apps" array anywhere in the file. This avoids loading huge
            # steam.json files entirely into memory.
            if not apps_list:
                # Streaming parser that reads the file in chunks and extracts
                # objects from the first "apps" array it finds. This keeps
                # peak memory much lower than loading the entire file.
                apps_list = []
                try:
                    self._log_and_status("steam_processor: starting streaming fallback parse", 0)
                    chunk_size = 64 * 1024
                    buffer = ''
                    found_array = False
                    end_of_array = False
                    with open(input_json_path, 'r', encoding='utf-8') as fh:
                        while True:
                            chunk = fh.read(chunk_size)
                            if not chunk:
                                # EOF
                                break
                            buffer += chunk

                            if not found_array:
                                apps_key_pos = buffer.find('"apps"')
                                if apps_key_pos == -1:
                                    apps_key_pos = buffer.find("'apps'")
                                if apps_key_pos != -1:
                                    # find '[' after apps key
                                    bracket_pos = buffer.find('[', apps_key_pos)
                                    if bracket_pos != -1:
                                        # drop everything before the '[', keep rest
                                        buffer = buffer[bracket_pos+1:]
                                        found_array = True
                                        self._log_and_status("steam_processor: located 'apps' array; beginning to extract objects", 0)
                                    else:
                                        # keep a bit of overlap in buffer
                                        if len(buffer) > 1024:
                                            buffer = buffer[-1024:]
                                        continue

                            if found_array and not end_of_array:
                                idx = 0
                                length = len(buffer)
                                while idx < length:
                                    # Skip whitespace and commas
                                    if buffer[idx] in ' \t\r\n,':
                                        idx += 1
                                        continue
                                    if buffer[idx] == ']':
                                        end_of_array = True
                                        break
                                    if buffer[idx] != '{':
                                        # Skip unexpected characters
                                        idx += 1
                                        continue

                                    # Parse a balanced object
                                    start = idx
                                    depth = 0
                                    in_string = False
                                    escape = False
                                    while idx < length:
                                        ch = buffer[idx]
                                        if in_string:
                                            if escape:
                                                escape = False
                                            elif ch == '\\':
                                                escape = True
                                            elif ch == '"':
                                                in_string = False
                                        else:
                                            if ch == '"':
                                                in_string = True
                                            elif ch == '{':
                                                depth += 1
                                            elif ch == '}':
                                                depth -= 1
                                                if depth == 0:
                                                    idx += 1
                                                    break
                                        idx += 1

                                    # If we didn't finish a full object, read more
                                    if depth != 0:
                                        break

                                    obj_text = buffer[start:idx]
                                    try:
                                        obj = json.loads(obj_text)
                                        apps_list.append(obj)
                                        # Periodically log streaming progress
                                        if len(apps_list) % 5000 == 0:
                                            self._log_and_status(f"steam_processor: streaming parsed {len(apps_list)} app objects", 0)
                                    except Exception:
                                        # ignore parse errors for individual objects
                                        self._log_and_status("steam_processor: failed to parse an object from stream (skipped)", 0)
                                        pass

                                # Trim processed part of the buffer to keep memory small
                                if end_of_array:
                                    # no need to keep anything further
                                    buffer = ''
                                    break
                                else:
                                    # keep the tail (unprocessed part)
                                    if idx < length:
                                        buffer = buffer[idx:]
                                    else:
                                        buffer = ''
                    # done reading
                    self._log_and_status(f"steam_processor: streaming parse complete, found {len(apps_list)} objects", 0)
                except Exception:
                    apps_list = []
                    self._log_and_status("steam_processor: streaming parse failed with exception", 0)
            
            # Sort apps_list by appid to ensure we process lower IDs first (usually main games)
            # This allows us to handle duplicates by simply keeping the first one seen
            def get_app_id(app):
                if isinstance(app, dict):
                    aid = app.get('appid')
                    if isinstance(aid, (int, str)):
                        try:
                            return int(aid)
                        except ValueError:
                            pass
                return float('inf')
            
            try:
                apps_list.sort(key=get_app_id)
            except Exception:
                pass

            if not apps_list:
                QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("No apps found in Steam JSON file", 5000))
                return False

            # Process the apps list

            
            # Define exclusion terms and patterns
            exclusion_terms = [
                "soundtrack",
                "trailer",
                "dedicated server",
                "Closed Beta",
                "test app",
                "beta",
                "sdk",
                "editor",
                "tool",
                "dlc", 
                "add-on",
                "plugins",
                "plug-ins",
                "Activation",
                "Artwork",
                "Wallpaper",
                "Preorder"
            ]
            
            regex_exclusion_patterns = [
                r"(?:\s[A-Za-z0-9]+)?\sDemo$",
                r"(?:\s[A-Za-z0-9]+)?\sAddons$",
                r"(?:\s[A-Za-z0-9]+)?\sBeta$",
                r"(?:\s[A-Za-z0-9]+)?\sTest$",
                r"(?:\s[A-Za-z0-9]+)?\sOST\s.*$",
                r"(?:\s[A-Za-z0-9]+)?\sServer$",
                r"(?:\s[A-Za-z0-9]+)?\sPatch$",
                r"(?:\s[A-Za-z0-9]+)?\sSet$"
            ]
            compiled_regex_exclusions = [re.compile(p, re.IGNORECASE) for p in regex_exclusion_patterns]
            
            # Filter out non-games, empty names, and duplicates
            seen_app_ids = set()  # Track seen app IDs to filter duplicates
            seen_app_names = set()   # Track seen app names to detect duplicates
            
            total_apps = len(apps_list)
            
            # Prepare output file path
            cache_file_path = os.path.join(constants.APP_ROOT_DIR, STEAM_FILTERED_TXT)
            processed_count = 0
            
            # Counters for filter diagnostics
            filter_counts = {
                'input_total': 0,
                'missing_fields': 0,
                'duplicate_app_id': 0,
                'duplicate_name': 0,
                'wrong_type': 0,
                'too_short': 0,
                'exclusion_term': 0,
                'regex_exclusion': 0,
                'common_words': 0,
                'accepted': 0
            }
            
            first_accepted = None  # Store first accepted app for debug
            first_rejected_reasons = []  # Store first few rejections with reasons
            sample_apps_logged = False  # Flag to log sample structure once
            
            with open(cache_file_path, 'w', encoding='utf-8') as f:
                for i, app in enumerate(apps_list):
                    filter_counts['input_total'] += 1
                    
                    # Log structure of first few apps to diagnose the format
                    if i < 3 and not sample_apps_logged:
                        self._log_and_status(f"steam_processor: SAMPLE APP STRUCTURE (first {min(3, len(apps_list))} apps):", 0)
                        self._log_and_status(f"  App {i} keys: {list(app.keys()) if isinstance(app, dict) else 'NOT A DICT'}", 0)
                        if isinstance(app, dict):
                            self._log_and_status(f"  App {i} content: {str(app)[:200]}...", 0)
                        if i == 2:
                            sample_apps_logged = True
                    
                    # Update progress periodically
                    if i % 5000 == 0:
                        msg = f"Processing app {i}/{total_apps}..."
                        QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(msg, 0))
                        self._log_and_status(f"steam_processor: {msg}", 0)
                    
                    if not isinstance(app, dict):
                        filter_counts['missing_fields'] += 1
                        continue
                    
                    # Try multiple possible field names for app ID
                    app_id = app.get('steam_id') or app.get('appid') or app.get('app_id') or app.get('id')
                    app_name = app.get('name')
                    
                    # Skip if missing required fields or empty name
                    if not app_id or not app_name or not app_name.strip():
                        filter_counts['missing_fields'] += 1
                        if len(first_rejected_reasons) < 3:
                            first_rejected_reasons.append((app, 'missing_fields'))
                        continue
                    
                    # Convert app_id to string
                    app_id = str(app_id)
                    
                    # Skip duplicates by app_id
                    if app_id in seen_app_ids:
                        filter_counts['duplicate_app_id'] += 1
                        continue
                    
                    # Check for duplicate names (case insensitive)
                    app_name_lower = app_name.lower()
                    if app_name_lower in seen_app_names:
                        filter_counts['duplicate_name'] += 1
                        self._log_and_status(f"steam_processor: DUPLICATE_NAME: id={app_id} name={app_name}", 0)
                        # Since we sorted by ID, the existing one is the one we want (lower ID)
                        continue
                    
                    # Skip non-games if type is specified
                    app_type = app.get('type', '').lower()
                    if app_type and app_type not in ('game', 'dlc', 'application'):
                        filter_counts['wrong_type'] += 1
                        if len(first_rejected_reasons) < 3:
                            first_rejected_reasons.append((app, f'wrong_type: {app_type}'))
                        continue
                        
                    # Skip very short names or names with just common words
                    # (removed the too_short filter per user request)

                    # Skip if name contains exclusion terms
                    if any(term in app_name_lower for term in exclusion_terms):
                        filter_counts['exclusion_term'] += 1
                        self._log_and_status(f"steam_processor: EXCLUSION_TERM: id={app_id} name={app_name}", 0)
                        continue
                        
                    # Skip if name matches regex exclusion patterns
                    if any(rx.search(app_name) for rx in compiled_regex_exclusions):
                        filter_counts['regex_exclusion'] += 1
                        self._log_and_status(f"steam_processor: REGEX_EXCLUSION: id={app_id} name={app_name}", 0)
                        continue
                        
                    # Skip names that are just common words
                    common_words = ["game", "the", "of", "and", "a", "an", "in", "on", "to", "for", "with", "by", "about"]
                    words = app_name.lower().split()
                    if all(word in common_words for word in words):
                        filter_counts['common_words'] += 1
                        self._log_and_status(f"steam_processor: COMMON_WORDS: id={app_id} name={app_name}", 0)
                        continue
                    
                    # Add to tracking sets
                    seen_app_ids.add(app_id)
                    seen_app_names.add(app_name_lower)
                    
                    # Add to cache
                    local_title_cache[app_id] = app_name
                    
                    # Write to file immediately
                    f.write(f"{app_id}\t{app_name}\n")
                    processed_count += 1
                    filter_counts['accepted'] += 1
                    if first_accepted is None:
                        first_accepted = app
                    # Log progress of written entries every few thousand
                    if processed_count % 5000 == 0:
                        self._log_and_status(f"steam_processor: wrote {processed_count} filtered entries to {STEAM_FILTERED_TXT}", 0)
            
            # Assign local cache to main window
            self.main_window.steam_title_cache = local_title_cache
            
            # Log filter diagnostics
            self._log_and_status(f"steam_processor: FILTER DIAGNOSTICS", 0)
            self._log_and_status(f"  Input total: {filter_counts['input_total']}", 0)
            self._log_and_status(f"  Rejected (missing fields): {filter_counts['missing_fields']}", 0)
            self._log_and_status(f"  Rejected (duplicate app_id): {filter_counts['duplicate_app_id']}", 0)
            self._log_and_status(f"  Rejected (duplicate name): {filter_counts['duplicate_name']}", 0)
            self._log_and_status(f"  Rejected (wrong type): {filter_counts['wrong_type']}", 0)
            self._log_and_status(f"  Rejected (too short): {filter_counts['too_short']}", 0)
            self._log_and_status(f"  Rejected (exclusion term): {filter_counts['exclusion_term']}", 0)
            self._log_and_status(f"  Rejected (regex exclusion): {filter_counts['regex_exclusion']}", 0)
            self._log_and_status(f"  Rejected (common words): {filter_counts['common_words']}", 0)
            self._log_and_status(f"  Accepted (passed all filters): {filter_counts['accepted']}", 0)
            
            if first_accepted:
                self._log_and_status(f"steam_processor: FIRST ACCEPTED APP: id={first_accepted.get('appid')} name={first_accepted.get('name')}", 0)
            
            if first_rejected_reasons:
                self._log_and_status(f"steam_processor: SAMPLE REJECTED APPS:", 0)
                for app, reason in first_rejected_reasons:
                    self._log_and_status(f"  id={app.get('appid')} name={app.get('name')} type={app.get('type')} reason={reason}", 0)
            
            if processed_count == 0:
                QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("No valid games found in Steam JSON after filtering", 5000))
                self._log_and_status("steam_processor: no valid games found after filtering", 0)
                return False
            
            # Store the cache file path - make sure it's the .txt file
            self.main_window.filtered_steam_cache_file_path = cache_file_path

            
            # Create normalized index for better matching
            self._log_and_status(f"steam_processor: creating normalized index from {processed_count} entries", 0)
            self.steam_cache_manager.create_normalized_steam_index()
            self._log_and_status("steam_processor: normalized index creation complete", 0)
            
            return True
            
        except json.JSONDecodeError:
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent("Error: Invalid JSON file format", 5000))
            return False
        except Exception as e:
            import traceback

            traceback.print_exc()
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Error processing Steam JSON: {str(e)}", 5000))
            return False

    def _disable_ui_elements(self):
        """Disable UI elements during processing"""
        # Disable main tabs
        for i in range(self.main_window.tabs.count()):
            tab = self.main_window.tabs.widget(i)
            tab.setEnabled(False)
        
        # Disable specific buttons
        if hasattr(self.main_window, 'process_steam_json_button'):
            self.main_window.process_steam_json_button.setEnabled(False)
        if hasattr(self.main_window, 'update_steam_json_button'):
            self.main_window.update_steam_json_button.setEnabled(False)
        
        # Process events to update UI
        QCoreApplication.processEvents()

    def _enable_ui_elements(self):
        """Re-enable UI elements after processing"""
        # Re-enable main tabs
        for i in range(self.main_window.tabs.count()):
            tab = self.main_window.tabs.widget(i)
            tab.setEnabled(True)
        
        # Re-enable specific buttons
        if hasattr(self.main_window, 'process_steam_json_button'):
            self.main_window.process_steam_json_button.setEnabled(True)
        if hasattr(self.main_window, 'update_steam_json_button'):
            self.main_window.update_steam_json_button.setEnabled(True)
        
        # Process events to update UI
        QCoreApplication.processEvents()
