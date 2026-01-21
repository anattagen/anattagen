# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import json
import os

# APP THEMES
# ///////////////////////////////////////////////////////////////
class JsonThemes(object):
    # INIT SETTINGS
    # ///////////////////////////////////////////////////////////////
    def __init__(self):
        super(JsonThemes, self).__init__()
        # DICTIONARY WITH SETTINGS
        self.items = {}

    def load_theme(self, theme_file):
        if os.path.isfile(theme_file):
            try:
                with open(theme_file, "r", encoding='utf-8') as reader:
                    self.items = json.loads(reader.read())
            except Exception as e:
                print(f"Error loading theme {theme_file}: {e}")

    def load_json_theme(self, theme_file):
        self.load_theme(theme_file)

    @property
    def stylesheet(self):
        # Attempt to locate style.qss in ../styles/style.qss relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_dir)
        style_path = os.path.join(gui_dir, "styles", "style.qss")

        if not os.path.exists(style_path):
            return ""

        with open(style_path, "r", encoding='utf-8') as f:
            style_content = f.read()

        # Default fallback values to prevent parse errors if keys are missing
        defaults = {
            "bg_one": "#2c313c",
            "bg_two": "#343b47",
            "bg_three": "#3a414d",
            "text_color": "#ffffff",
            "accent_color": "#00aaff"
        }
        theme_items = defaults.copy()
        theme_items.update(self.items)

        # Replace placeholders in QSS with values from the loaded JSON items
        for key, value in theme_items.items():
            if isinstance(value, str):
                style_content = style_content.replace(f"@{key}", value)

        return style_content