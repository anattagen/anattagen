import os
from PyQt6.QtWidgets import QApplication

# gui internals (correct ones)
from Python.ui.theme.gui.core.json_themes import JsonThemes
from Python.ui.theme.gui.core.json_settings import Settings


class ThemeLoader:
    """
    Adapter layer between anattagen and gui's JSON theme system.
    """

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    gui_DIR = os.path.join(BASE_DIR, "gui")
    THEMES_DIR = os.path.join(gui_DIR, "themes")

    @classmethod
    def apply(cls, app: QApplication, theme: str = "default"):
        if not isinstance(app, QApplication):
            raise TypeError("ThemeLoader.apply() requires a QApplication instance")

        theme_path = os.path.join(cls.THEMES_DIR, f"{theme}.json")

        if not os.path.exists(theme_path):
            raise FileNotFoundError(theme_path)

        # ✅ Settings auto-load on instantiation
        Settings()

        # Load theme JSON and generate stylesheet
        theme_engine = JsonThemes()
        theme_engine.load_json_theme(theme_path)

        # Apply stylesheet to the app
        app.setStyleSheet(theme_engine.stylesheet)