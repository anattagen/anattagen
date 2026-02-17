import logging
import time
import requests
try:
    import cloudscraper
except ImportError:
    cloudscraper = None
from urllib.parse import quote, unquote, urlparse
from bs4 import BeautifulSoup

class PCGWManager:
    """
    Manages interactions with the PCGamingWiki Cargo API.
    PCGamingWiki migrated from Semantic MediaWiki to Cargo for backend data.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        if cloudscraper:
            self.session = cloudscraper.create_scraper()
            self.session.headers.update({k: v for k, v in self.headers.items() if k != 'User-Agent'})
        else:
            self.session = requests.Session()
            self.session.headers.update(self.headers)
        
        self.api_url = "https://www.pcgamingwiki.com/w/api.php"

    def fetch_data(self, game_name, steam_id=None):
        """
        Fetches metadata from PCGamingWiki using the Cargo API.
        
        Args:
            game_name (str): The name of the game to search for.
            steam_id (str, optional): The Steam AppID to query directly.
            
        Returns:
            dict: A dictionary containing parsed PCGW data, or None if failed.
        """
        pcgw_data = {}
        page_id = None
        page_name = None

        # 1. Try to query by Steam AppID using Cargo API
        if steam_id and str(steam_id) not in ['NOT_FOUND_IN_DATA', 'ITEM_IS_NONE', '']:
            try:
                time.sleep(0.5)  # Rate limiting
                params = {
                    'action': 'cargoquery',
                    'tables': 'Infobox_game',
                    'fields': 'Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Publishers,Infobox_game.Engines,Infobox_game.Released,Infobox_game.Genres,Infobox_game.Modes,Infobox_game.Series,Infobox_game.Monetization,Infobox_game.Microtransactions,Infobox_game.DRM,Infobox_game.Steam_AppID',
                    'where': f'Infobox_game.Steam_AppID HOLDS "{steam_id}"',
                    'format': 'json',
                    'limit': '1'
                }
                
                response = self.session.get(self.api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'cargoquery' in data and len(data['cargoquery']) > 0:
                        result = data['cargoquery'][0]['title']
                        page_id = result.get('PageID')
                        page_name = result.get('Page')
                        pcgw_data['Developers'] = result.get('Developers', '')
                        pcgw_data['Publishers'] = result.get('Publishers', '')
                        pcgw_data['Engines'] = result.get('Engines', '')
                        pcgw_data['Released'] = result.get('Released', '')
                        pcgw_data['Genres'] = result.get('Genres', '')
                        pcgw_data['Modes'] = result.get('Modes', '')
                        pcgw_data['Series'] = result.get('Series', '')
                        pcgw_data['Monetization'] = result.get('Monetization', '')
                        pcgw_data['Microtransactions'] = result.get('Microtransactions', '')
                        pcgw_data['DRM'] = result.get('DRM', '')
                        pcgw_data['Steam_AppID'] = result.get('Steam AppID', '')
                        logging.info(f"Found PCGW data via Steam AppID {steam_id}: {page_name}")
                    else:
                        logging.warning(f"No PCGW data found for Steam AppID {steam_id}")
                else:
                    logging.warning(f"PCGW Cargo API returned status {response.status_code}")
            except Exception as e:
                logging.error(f"PCGW Cargo query by AppID failed: {e}")

        # 2. If no data found by AppID, try searching by game name
        if not page_name and game_name:
            try:
                time.sleep(0.5)
                params = {
                    'action': 'cargoquery',
                    'tables': 'Infobox_game',
                    'fields': 'Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Publishers,Infobox_game.Engines,Infobox_game.Released,Infobox_game.Genres,Infobox_game.Modes,Infobox_game.Series,Infobox_game.Monetization,Infobox_game.Microtransactions,Infobox_game.DRM,Infobox_game.Steam_AppID',
                    'where': f'Infobox_game._pageName="{game_name}"',
                    'format': 'json',
                    'limit': '1'
                }
                
                response = self.session.get(self.api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'cargoquery' in data and len(data['cargoquery']) > 0:
                        result = data['cargoquery'][0]['title']
                        page_id = result.get('PageID')
                        page_name = result.get('Page')
                        pcgw_data['Developers'] = result.get('Developers', '')
                        pcgw_data['Publishers'] = result.get('Publishers', '')
                        pcgw_data['Engines'] = result.get('Engines', '')
                        pcgw_data['Released'] = result.get('Released', '')
                        pcgw_data['Genres'] = result.get('Genres', '')
                        pcgw_data['Modes'] = result.get('Modes', '')
                        pcgw_data['Series'] = result.get('Series', '')
                        pcgw_data['Monetization'] = result.get('Monetization', '')
                        pcgw_data['Microtransactions'] = result.get('Microtransactions', '')
                        pcgw_data['DRM'] = result.get('DRM', '')
                        pcgw_data['Steam_AppID'] = result.get('Steam AppID', '')
                        logging.info(f"Found PCGW data by name: {page_name}")
            except Exception as e:
                logging.error(f"PCGW Cargo query by name failed: {e}")

        # 3. Get save/config locations from Cargo tables
        if page_name:
            self._fetch_save_locations(page_name, pcgw_data)
            self._fetch_config_locations(page_name, pcgw_data)
            self._fetch_video_settings(page_name, pcgw_data)
            self._fetch_input_settings(page_name, pcgw_data)

        return pcgw_data if pcgw_data else None

    def _fetch_save_locations(self, page_name, pcgw_data):
        """Fetch save game locations from Cargo API."""
        try:
            time.sleep(0.5)
            params = {
                'action': 'cargoquery',
                'tables': 'Saves',
                'fields': 'Saves.System,Saves.Location,Saves.Cloud',
                'where': f'Saves._pageName="{page_name}"',
                'format': 'json',
                'limit': '50'
            }
            
            response = self.session.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                save_locations = {}
                
                if 'cargoquery' in data and len(data['cargoquery']) > 0:
                    for item in data['cargoquery']:
                        result = item['title']
                        system = result.get('System', 'Unknown')
                        location = result.get('Location', '')
                        cloud = result.get('Cloud', '')
                        
                        if location:
                            if system not in save_locations:
                                save_locations[system] = []
                            
                            save_entry = {'path': location}
                            if cloud:
                                save_entry['cloud'] = cloud
                            
                            save_locations[system].append(save_entry)
                    
                    logging.info(f"Found {len(data['cargoquery'])} save locations for {page_name}")
                
                pcgw_data['save_locations'] = save_locations
            else:
                logging.warning(f"PCGW save locations query returned status {response.status_code}")
                pcgw_data['save_locations'] = {}
                
        except Exception as e:
            logging.error(f"Failed to fetch save locations: {e}")
            pcgw_data['save_locations'] = {}

    def _fetch_config_locations(self, page_name, pcgw_data):
        """Fetch config file locations from Cargo API."""
        try:
            time.sleep(0.5)
            params = {
                'action': 'cargoquery',
                'tables': 'Config',
                'fields': 'Config.System,Config.Location,Config.Cloud',
                'where': f'Config._pageName="{page_name}"',
                'format': 'json',
                'limit': '50'
            }
            
            response = self.session.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                config_locations = {}
                
                if 'cargoquery' in data and len(data['cargoquery']) > 0:
                    for item in data['cargoquery']:
                        result = item['title']
                        system = result.get('System', 'Unknown')
                        location = result.get('Location', '')
                        cloud = result.get('Cloud', '')
                        
                        if location:
                            if system not in config_locations:
                                config_locations[system] = []
                            
                            config_entry = {'path': location}
                            if cloud:
                                config_entry['cloud'] = cloud
                            
                            config_locations[system].append(config_entry)
                    
                    logging.info(f"Found {len(data['cargoquery'])} config locations for {page_name}")
                
                pcgw_data['config_locations'] = config_locations
            else:
                logging.warning(f"PCGW config locations query returned status {response.status_code}")
                pcgw_data['config_locations'] = {}
                
        except Exception as e:
            logging.error(f"Failed to fetch config locations: {e}")
            pcgw_data['config_locations'] = {}

    def _fetch_video_settings(self, page_name, pcgw_data):
        """Fetch video settings from Cargo API."""
        try:
            time.sleep(0.5)
            params = {
                'action': 'cargoquery',
                'tables': 'Video_settings',
                'fields': 'Video_settings.Widescreen_resolution,Video_settings.Multimonitor,Video_settings.Ultra_widescreen,Video_settings.4K_ultra_HD,Video_settings.Field_of_view,Video_settings.Windowed,Video_settings.Borderless_fullscreen_windowed,Video_settings.Anisotropic_filtering,Video_settings.Anti_aliasing,Video_settings.Vertical_sync,Video_settings.FPS_limit',
                'where': f'Video_settings._pageName="{page_name}"',
                'format': 'json',
                'limit': '1'
            }
            
            response = self.session.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'cargoquery' in data and len(data['cargoquery']) > 0:
                    result = data['cargoquery'][0]['title']
                    video_settings = {}
                    
                    for key, value in result.items():
                        if value:
                            # Clean up key names
                            clean_key = key.replace('Video settings.', '').replace('_', ' ')
                            video_settings[clean_key] = value
                    
                    if video_settings:
                        pcgw_data['video_settings'] = video_settings
                        logging.info(f"Found video settings for {page_name}")
                
        except Exception as e:
            logging.error(f"Failed to fetch video settings: {e}")

    def _fetch_input_settings(self, page_name, pcgw_data):
        """Fetch input settings from Cargo API."""
        try:
            time.sleep(0.5)
            params = {
                'action': 'cargoquery',
                'tables': 'Input',
                'fields': 'Input.Remapping,Input.Mouse_acceleration,Input.Controller_support,Input.Full_controller_support,Input.Controller_remapping,Input.Tracked_controllers_support,Input.VR_motion_controllers_support',
                'where': f'Input._pageName="{page_name}"',
                'format': 'json',
                'limit': '1'
            }
            
            response = self.session.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'cargoquery' in data and len(data['cargoquery']) > 0:
                    result = data['cargoquery'][0]['title']
                    input_settings = {}
                    
                    for key, value in result.items():
                        if value:
                            # Clean up key names
                            clean_key = key.replace('Input.', '').replace('_', ' ')
                            input_settings[clean_key] = value
                    
                    if input_settings:
                        pcgw_data['input_settings'] = input_settings
                        logging.info(f"Found input settings for {page_name}")
                
        except Exception as e:
            logging.error(f"Failed to fetch input settings: {e}")
