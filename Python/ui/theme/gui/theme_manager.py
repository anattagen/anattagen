import os
from PyQt6.QtWidgets import QApplication
from .core import json_settings, json_themes

class ThemeManager:
    """
    Centralized runtime theme switcher for the GUI.
    """

    THEMES_DIR = os.path.join(os.path.dirname(__file__), "themes")

    @classmethod
    def available_themes(cls):
        """Return a list of theme JSON files without extensions."""
        return [f.replace(".json", "") for f in os.listdir(cls.THEMES_DIR) if f.endswith(".json")]

    @classmethod
    def apply_theme(cls, app: QApplication, theme_name: str):
        theme_file = os.path.join(cls.THEMES_DIR, f"{theme_name}.json")
        if not os.path.exists(theme_file):
            raise FileNotFoundError(f"Theme not found: {theme_file}")

        # Load settings (required by framework)
        json_settings.Settings()

        # Load the theme JSON
        theme_engine = json_themes.JsonThemes()

        # Most vendored frameworks allow this method
        if hasattr(theme_engine, "load_theme"):
            theme_engine.load_theme(theme_file)
        elif hasattr(theme_engine, "set_theme"):
            theme_engine.set_theme(theme_file)
        elif hasattr(theme_engine, "load"):
            theme_engine.load(theme_file)
        else:
            raise RuntimeError("Unsupported JsonThemes API")

        # Apply generated stylesheet
        if not hasattr(theme_engine, "stylesheet"):
            raise RuntimeError("Theme engine did not produce a stylesheet")

        app.setStyleSheet(theme_engine.stylesheet)
