import os
import json
import re
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QCoreApplication
from Python.ui.name_utils import normalize_name_for_matching
from Python.ui.steam_cache import STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE # Only import constants, not functions

# Import custom events from main_window_new
from Python.main_window_new import _StatusUpdateEvent, _EnableUIEvent

class SteamProcessor:
    def __init__(self, main_window, steam_cache_manager):
        self.main_window = main_window
        self.steam_cache_manager = steam_cache_manager

    def prompt_and_process_steam_json(self):
        """Prompt user to select and process Steam JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, "Select Steam JSON file", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            # Backup existing cache files before processing using the SteamCacheManager
            self.steam_cache_manager.backup_cache_files()

            # Disable UI elements
            self._disable_ui_elements()
            self.main_window.statusBar().showMessage("Please be patient as the steam.json file is cached...", 0)

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
            self.main_window.statusBar().showMessage(f"Steam JSON file not found: {input_json_path}", 5000)
            return False
        
        try:
            # Process the file
            self.main_window.statusBar().showMessage(f"Processing Steam JSON: {input_json_path}", 0)
            
            # Store the path for later reference
            self.main_window.steam_json_file_path = input_json_path
            
            # Load the JSON data
            with open(input_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Filter and extract title data
            self.main_window.steam_title_cache = {}
            
            # Handle different JSON structures
            apps_list = []
            
            if isinstance(data, dict):
                # Check if it's the standard Steam API format
                if 'applist' in data and 'apps' in data['applist']:
                    apps_list = data['applist']['apps']
                elif 'response' in data and 'apps' in data['response']:
                    apps_list = data['response']['apps']
                else:
                    # Fallback for other structures
                    apps_list = data.get('apps', [])
            elif isinstance(data, list):
                # Direct list of apps
                apps_list = data
            
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
            filtered_apps = []
            seen_app_ids = set()  # Track seen app IDs to filter duplicates
            seen_app_names = {}   # Track seen app names to detect duplicates
            
            for app in apps_list:
                if not isinstance(app, dict):

                    continue
                    
                app_id = app.get('appid')
                app_name = app.get('name')
                
                # Skip if missing required fields or empty name
                if not app_id or not app_name or not app_name.strip():

                    continue
                
                # Convert app_id to string
                app_id = str(app_id)
                
                # Skip duplicates by app_id
                if app_id in seen_app_ids:

                    continue
                
                # Check for duplicate names (case insensitive)
                app_name_lower = app_name.lower()
                if app_name_lower in seen_app_names:
                    existing_id = seen_app_names[app_name_lower]

                    # Keep the one with the lower app_id (usually the original/main game)
                    if int(app_id) < int(existing_id):
                        # Replace the existing entry

                        # Remove the old entry from filtered_apps
                        filtered_apps = [app for app in filtered_apps if app[0] != existing_id]
                        # Update the seen_app_ids and seen_app_names
                        seen_app_ids.remove(existing_id)
                        seen_app_names[app_name_lower] = app_id
                    else:
                        # Skip this entry

                        continue
                
                # Skip non-games if type is specified
                app_type = app.get('type', '').lower()
                if app_type and app_type not in ('game', 'dlc', 'application'):

                    continue
                    
                # Skip very short names or names with just common words
                if len(app_name) < 4:

                    continue

                # Skip if name contains exclusion terms
                if any(term in app_name_lower for term in exclusion_terms):

                    continue
                    
                # Skip if name matches regex exclusion patterns
                if any(rx.search(app_name) for rx in compiled_regex_exclusions):

                    continue
                    
                # Skip names that are just common words
                common_words = ["game", "the", "of", "and", "a", "an", "in", "on", "to", "for", "with", "by", "about"]
                words = app_name.lower().split()
                if all(word in common_words for word in words):

                    continue
                
                # Add to tracking sets
                seen_app_ids.add(app_id)
                seen_app_names[app_name_lower] = app_id
                
                # Add to filtered list
                filtered_apps.append((app_id, app_name))
                
                # Add to cache
                self.main_window.steam_title_cache[app_id] = app_name
            

            
            # Get the app's root directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            app_root_dir = os.path.dirname(os.path.dirname(script_dir))
            
            # Save filtered data to a text file in the app root directory
            cache_file_path = os.path.join(app_root_dir, STEAM_FILTERED_TXT)
            
            with open(cache_file_path, 'w', encoding='utf-8') as f:
                for app_id, app_name in filtered_apps:
                    # Use tab as separator (less likely to appear in game names than pipe)
                    f.write(f"{app_id}\t{app_name}\n")
            
            if os.path.exists(cache_file_path) and os.path.getsize(cache_file_path) > 0:
                pass
            else:
                pass

            # Store the cache file path - make sure it's the .txt file
            self.main_window.filtered_steam_cache_file_path = cache_file_path

            
            # Create normalized index for better matching
            self.steam_cache_manager.create_normalized_steam_index()
            
            return True
            
        except Exception as e:
            import traceback

            traceback.print_exc()
            self.main_window.statusBar().showMessage(f"Error processing Steam JSON: {str(e)}", 5000)
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
