import os
import logging

# No PyQt6 or qfluentwidgets imports at top level
from Python.models import AppConfig
from Python import constants

# Managers will be imported lazily
# from Python.managers.data_manager import DataManager
# from Python.managers.steam_manager import SteamManager
# from Python.managers.config_manager import ConfigManager

class FluentMainWindow:
    """
    Wrapper for the real FluentWindow.
    All PyQt widgets are created lazily after QApplication exists.
    """

    def __init__(self):
        self._window = None
        self.app_config = AppConfig()
        self.config_manager = None
        self.data_manager = None
        self.steam_manager = None

    def _create_window(self):
        """
        Lazily create the real FluentWindow and managers.
        This avoids constructing QWidgets before QApplication exists.
        """

        # Lazy imports
        from PyQt6.QtWidgets import QWidget
        from qfluentwidgets import FluentWindow, setTheme, Theme
        from Python.managers.config_manager import ConfigManager
        from Python.managers.data_manager import DataManager
        from Python.managers.steam_manager import SteamManager
        from Python.ui.deployment_tab import DeploymentTab
        from Python.ui.setup_tab import SetupTab
        from Python.ui.editor_tab import EditorTab
        from Python.ui.steam_cache import SteamCacheManager, STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE

        self.config_manager = ConfigManager()

        wrapper = self  # capture wrapper reference

        class RealFluentWindow(FluentWindow):
            def __init__(inner_self):
                super().__init__()

                # Set the theme
                setTheme(Theme.LIGHT if not wrapper.app_config.dark_mode else Theme.DARK)

                # Initialize managers safely
                wrapper.data_manager = DataManager(wrapper.app_config, inner_self)
                wrapper.steam_manager = SteamManager(wrapper.app_config, inner_self)

                # Create tabs
                self.setup_tab = SetupTab(inner_self, wrapper)
                self.deployment_tab = DeploymentTab(inner_self, wrapper)
                self.editor_tab = EditorTab(inner_self, wrapper)

                # Set up main navigation
                self.add_navigation_item(self.setup_tab, "Setup")
                self.add_navigation_item(self.deployment_tab, "Deployment")
                self.add_navigation_item(self.editor_tab, "Editor")

                # Optional: other FluentWindow setup (menus, toolbars, etc.)

            def add_navigation_item(inner_self, tab_widget, title):
                # Example placeholder for navigation setup
                inner_self.add_tab(tab_widget, title)

        self._window = RealFluentWindow()

    def show(self):
        """Ensure the window exists and then show it."""
        if self._window is None:
            self._create_window()
        self._window.show()

    def cleanup(self):
        """
        Safely cleanup managers and other resources.
        Call before app exit.
        """
        if self.data_manager:
            self.data_manager.cleanup()
            self.data_manager = None
        if self.steam_manager:
            self.steam_manager.cleanup()
            self.steam_manager = None
        if self.config_manager:
            self.config_manager.cleanup()
            self.config_manager = None
        self._window = None

    # ------------------------------
    # Status bar update
    # ------------------------------
    def update_status(self, message, timeout=3000):
        if self._window is None:
            logging.warning("Cannot update status before main window exists")
            return
        self._window.statusBar().showMessage(message, timeout)

    # ------------------------------
    # Steam cache helper
    # ------------------------------
    def refresh_steam_cache(self):
        try:
            if self._window:
                self._window.steam_cache_manager.refresh()
            self.update_status("Steam cache refreshed", 5000)
        except Exception as e:
            logging.error(f"Steam cache refresh failed: {e}")
            self.message_box("Error", f"Steam cache refresh failed:\n{e}")

    # ------------------------------
    # Editor highlight
    # ------------------------------
    def highlight_editor(self, editor_tab, lines, color="#FFFF00"):
        try:
            editor_tab.highlight_lines(lines, color)
        except Exception as e:
            logging.error(f"Editor highlight failed: {e}")
