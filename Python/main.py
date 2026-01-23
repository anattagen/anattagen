import sys
import os
import logging
import argparse
import traceback

# Force qfluentwidgets to use PyQt6
os.environ["QT_API"] = "pyqt6"

# Add the parent directory (anattagen) to the Python path
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

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description="Game Environment Manager - Main Application")
    parser.parse_known_args()  # Qt handles its own args

    setup_logging()

    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError as e:
        logging.error(f"PyQt6 import failed: {e}")
        return

    # 1️⃣ Create QApplication first
    app = QApplication(sys.argv)
    from Python.main_window_fluent import FluentMainWindow

    window_wrapper = FluentMainWindow()
    window_wrapper.show()
    sys.exit(app.exec())

    # 5️⃣ Start event loop
    try:
        sys.exit(app.exec())
    finally:
        # Cleanup any resources
        window_wrapper.cleanup()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")
