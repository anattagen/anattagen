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
                    'fields': 'Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Publishers,Infobox_game.Engines,Infobox_game.Released',
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
                    'fields': 'Infobox_game._pageID=PageID,Infobox_game._pageName=Page,Infobox_game.Developers,Infobox_game.Publishers,Infobox_game.Engines,Infobox_game.Released',
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
                        logging.info(f"Found PCGW data by name: {page_name}")
            except Exception as e:
                logging.error(f"PCGW Cargo query by name failed: {e}")

        # 3. Get save/config locations by parsing the page HTML
        if page_id:
            try:
                time.sleep(0.5)
                params = {
                    'action': 'parse',
                    'pageid': page_id,
                    'format': 'json',
                    'prop': 'text'
                }
                
                response = self.session.get(self.api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'parse' in data and 'text' in data['parse']:
                        html_content = data['parse']['text']['*']
                        soup = BeautifulSoup(html_content, 'html.parser')
                        self._parse_locations_from_soup(soup, pcgw_data)
            except Exception as e:
                logging.error(f"Failed to parse PCGW page HTML: {e}")

        return pcgw_data if pcgw_data else None

    def _parse_locations_from_soup(self, soup, pcgw_data):
        """Parse save and config locations from the page HTML."""
        save_locations = {}
        config_locations = {}
        
        content = soup.find('div', class_='mw-parser-output')
        if content:
            headers = content.find_all(['h2', 'h3', 'h4'])
            for header in headers:
                header_text = header.get_text(strip=True)
                if 'Save game data location' in header_text:
                    next_elem = header.find_next(['ul', 'table'])
                    if next_elem:
                        self._parse_locations(next_elem, save_locations)
                elif 'Configuration file' in header_text or 'Config file' in header_text:
                    next_elem = header.find_next(['ul', 'table'])
                    if next_elem:
                        self._parse_locations(next_elem, config_locations)
        
        pcgw_data['save_locations'] = save_locations
        pcgw_data['config_locations'] = config_locations

    def _parse_locations(self, element, locations_dict):
        """Helper to parse location lists or tables."""
        if element.name == 'ul':
            lis = element.find_all('li')
            for li in lis:
                text = li.get_text(strip=True)
                if ':' in text:
                    platform, path = text.split(':', 1)
                    platform = platform.strip()
                    path = path.strip()
                    if platform not in locations_dict:
                        locations_dict[platform] = []
                    locations_dict[platform].append(path)
        elif element.name == 'table':
            rows = element.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    platform = cells[0].get_text(strip=True)
                    path = cells[1].get_text(strip=True)
                    if platform not in locations_dict:
                        locations_dict[platform] = []
                    locations_dict[platform].append(path)
