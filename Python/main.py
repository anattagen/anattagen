import sys
import os
import logging
from PyQt6.QtWidgets import QApplication

# Add the parent directory (anattagen) to the Python path
# This allows for absolute imports from the project root (e.g., from Python.main_window_new)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Python.main_window_new import MainWindow

def setup_logging():
    """Set up logging to file and console."""
    log_file = os.path.join(script_dir, 'app.log')
    logging.basicConfig(
        level=logging.INFO,
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
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle("Material")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
