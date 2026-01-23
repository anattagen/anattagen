import sys
import os
import logging
import argparse
import traceback


# Add the parent directory (anattagen) to the Python path
# This allows for absolute imports from the project root (e.g., from Python.main_window_new)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Python import constants

def setup_logging():
    """Set up logging to file and console. Honor ANATTAGEN_LOG_LEVEL environment variable for verbosity."""
    log_file = os.path.join(project_root, 'app.log')
    level_name = os.environ.get('ANATTAGEN_LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"Starting application from {script_dir}")
    logging.info(f"Log file: {os.path.abspath(log_file)}")

def create_splash_screen():
    """Creates a simple splash screen."""
    #from PyQt6.QtWidgets import QSplashScreen
    #from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
    #from PyQt6.QtCore import Qt

    # Try to load a splash image from assets, otherwise create a generated one
    splash_path = os.path.join(constants.ASSETS_DIR, "splash.png")
    
    #if os.path.exists(splash_path):
    #    pixmap = QPixmap(splash_path)
    #else:
        # Generate a placeholder splash
    #    pixmap = QPixmap(400, 200)
    #    pixmap.fill(QColor("#2d2d2d"))
    #    painter = QPainter(pixmap)
    #    painter.setPen(QColor("#ffffff"))
    #    painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
    #    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Game Environment Manager")
    #    painter.end()
        
    #splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    #return splash

def main():
    """Main function to run the application."""
    # Handle CLI arguments
    parser = argparse.ArgumentParser(description="Game Environment Manager - Main Application")
    # Qt arguments are handled by QApplication, so we use parse_known_args
    parser.parse_known_args()

    setup_logging()

    from PyQt6.QtWidgets import QApplication, QSplashScreen
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
    from PyQt6.QtCore import Qt
    
    # Enable High DPI scaling
    #QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    #QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    #QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # splash = create_splash_screen()
    # splash.show()
    # app.processEvents()

    from qfluentwidgets import FluentWindow, NavigationItemPosition
    from Python.main_window_fluent import FluentMainWindow
    window = FluentMainWindow()
    # splash.finish(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")