import sys
import os
import logging
import argparse
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
# Add the parent directory (anattagen) to the Python path
# This allows for absolute imports from the project root (e.g., from Python.main_window_new)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Python.main_window_new import MainWindow

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
    # Handle CLI arguments
    parser = argparse.ArgumentParser(description="Game Environment Manager - Main Application")
    # Qt arguments are handled by QApplication, so we use parse_known_args
    parser.parse_known_args()

    setup_logging()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
