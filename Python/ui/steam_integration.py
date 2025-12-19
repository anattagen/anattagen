"""
Steam integration module - provides compatibility with Steam game library
"""

# Import all functions from the new modules
from Python.ui.steam_cache import (
    SteamCacheManager,
    STEAM_FILTERED_TXT,
    NORMALIZED_INDEX_CACHE
)

from Python.ui.steam_processor import (
    SteamProcessor
)

from Python.ui.steam_utils import (
    locate_and_exclude_manager_config,
    debug_steam_cache,
    debug_steam_cache_loading
)

# Export all the imported functions
__all__ = [
    'SteamCacheManager',
    'SteamProcessor',
    'locate_and_exclude_manager_config',
    'debug_steam_cache',
    'debug_steam_cache_loading',
    'STEAM_FILTERED_TXT',
    'NORMALIZED_INDEX_CACHE'
]
