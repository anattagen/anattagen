import sys
import os
import re
import configparser
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTextEdit,
    QScrollArea,
    QGridLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt


class SiteGenerator(QWidget):
    """Compact two-column site-level generator UI.

    - Left column: tag description
    - Right column: editable field
    - Values persisted to site/site_values.ini
    - Generates site/index.html by replacing known tags in site/index.set
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Site Generator")
        self.resize(820, 900)

        self.site_dir = os.path.dirname(__file__)
        self.index_set_path = os.path.join(self.site_dir, 'index.set')
        self.output_html_path = os.path.join(self.site_dir, 'index.html')
        self.ini_path = os.path.join(self.site_dir, 'site_values.ini')

        # Minimal known tags list (only these are replaced)
        # Theme-related tags removed — generator will only replace keys present in site_values.ini
        self.known_tags = {
            "[-|-]": "Project Name",
            "[TAGLINE]": "Tagline",
            "[VERSION]": "Version",
            "[REVISION]": "Installer Link",
            "[RSIZE]": "Release Size",
            "[RSHA1]": "SHA1",
            "[PORTABLE]": "Portable Link",
            "[RELEASEPG]": "Release Page",
            "[GITUSER]": "GitHub Username",
            "[RJ_PROJ]": "Project ID",
            "[GIT_WEB]": "Git Web Host",
            "[RDATE]": "Release Date",
        }

        self.tag_widgets = {}

        # load saved ini (only source of defaults now)
        self.saved_values = self.load_ini()

        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)

        # header buttons
        hdr = QHBoxLayout()
        save_btn = QPushButton('Save Settings')
        save_btn.clicked.connect(self.save_ini)
        gen_btn = QPushButton('Generate HTML')
        gen_btn.clicked.connect(self.generate_html)
        reset_btn = QPushButton('Load defaults')
        reset_btn.clicked.connect(self.reset_to_index_defaults)
        hdr.addWidget(save_btn)
        hdr.addWidget(gen_btn)
        hdr.addWidget(reset_btn)
        hdr.addStretch()
        root.addLayout(hdr)

        # scroll area with grid (desc | field)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setColumnStretch(0, 30)
        grid.setColumnStretch(1, 70)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        for tag, desc in self.known_tags.items():
            lbl = QLabel(desc)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

            # choose text edit for multiline tagline, lineedit otherwise
            if tag == '[TAGLINE]':
                edit = QTextEdit()
                edit.setAcceptRichText(False)
                edit.setFixedHeight(80)
            else:
                edit = QLineEdit()

            key = tag.strip('[]')
            # initial value: saved ini > literal tag
            if key in self.saved_values:
                init = self.saved_values[key]
            else:
                init = tag

            try:
                if isinstance(edit, QLineEdit):
                    edit.setText(init)
                else:
                    edit.setPlainText(init)
            except Exception:
                pass

            grid.addWidget(lbl, row, 0)
            grid.addWidget(edit, row, 1)
            self.tag_widgets[tag] = edit
            row += 1

        container.setLayout(grid)
        scroll.setWidget(container)
        root.addWidget(scroll)

    # theme parsing removed — site_values.ini is now authoritative for replacements

    def load_ini(self):
        cfg = configparser.ConfigParser()
        if not os.path.exists(self.ini_path):
            return {}
        try:
            cfg.read(self.ini_path, encoding='utf-8')
            if 'values' in cfg:
                return dict(cfg['values'])
        except Exception:
            return {}
        return {}

    def save_ini(self):
        cfg = configparser.ConfigParser()
        cfg['values'] = {}
        for tag, widget in self.tag_widgets.items():
            key = tag.strip('[]')
            try:
                if isinstance(widget, QLineEdit):
                    cfg['values'][key] = widget.text()
                else:
                    cfg['values'][key] = widget.toPlainText()
            except Exception:
                cfg['values'][key] = ''
        try:
            with open(self.ini_path, 'w', encoding='utf-8') as f:
                cfg.write(f)
            QMessageBox.information(self, 'Saved', f'Settings saved to {self.ini_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not save INI: {e}')

    def reset_to_index_defaults(self):
        for tag, widget in self.tag_widgets.items():
            val = self.index_defaults.get(tag, tag)
            try:
                if isinstance(widget, QLineEdit):
                    widget.setText(val)
                else:
                    widget.setPlainText(val)
            except Exception:
                pass

    def generate_html(self):
        try:
            if not os.path.exists(self.index_set_path):
                QMessageBox.critical(self, 'Error', f'index.set not found at {self.index_set_path}')
                return
            tpl = open(self.index_set_path, 'r', encoding='utf-8').read()
            out = tpl
            for tag, widget in self.tag_widgets.items():
                key = tag.strip('[]')
                try:
                    if isinstance(widget, QLineEdit):
                        val = widget.text()
                    else:
                        val = widget.toPlainText()
                except Exception:
                    val = ''

                # Only perform replacement if the key exists in saved_values (site_values.ini)
                if key in self.saved_values and self.saved_values.get(key) != '':
                    replacement = self.saved_values.get(key)
                    out = out.replace(tag, replacement)
            with open(self.output_html_path, 'w', encoding='utf-8') as f:
                f.write(out)
            # refresh saved_values in memory
            self.saved_values = {tag.strip('[]'): (w.text() if isinstance(w, QLineEdit) else w.toPlainText()) for tag, w in self.tag_widgets.items()}
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not generate HTML: {e}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SiteGenerator()
    w.show()
    sys.exit(app.exec())
