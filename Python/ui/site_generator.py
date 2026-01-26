import sys
import os
import re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QScrollArea, QMessageBox, QFrame, QTextEdit, QComboBox)
from PyQt6.QtCore import Qt

class SiteGenerator(QWidget): # temp
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Site Generator")
        self.resize(600, 800)
        self.template_content = ""
        self.tag_widgets = {}
        
        # Known tags with descriptions/defaults
        self.known_tags = {
            "[-|-]": {"desc": "Project Name", "type": "lineedit"},
            "[TAGLINE]": {"desc": "Tagline", "type": "textarea"},
            "[VERSION]": {"desc": "Version String", "type": "lineedit"},
            "[REVISION]": {"desc": "Installer/Revision Link Name", "type": "lineedit"},
            "[RSIZE]": {"desc": "Release Size (MB)", "type": "lineedit"},
            "[RSHA1]": {"desc": "SHA1 Hash", "type": "lineedit"},
            "[PORTABLE]": {"desc": "Portable Zip Link Name", "type": "lineedit"},
            "[RELEASEPG]": {"desc": "Release Page URL", "type": "lineedit"},
            "[GITUSER]": {"desc": "GitHub Username", "type": "lineedit"},
            "[PAYPAL]": {"desc": "PayPal Amount/Link", "type": "lineedit"},
            "[RJ_PROJ]": {"desc": "Project ID (Folder Name)", "type": "lineedit"},
            "[GIT_WEB]": {"desc": "Git Web Host (e.g. github.com)", "type": "lineedit"},
            "[RDATE]": {"desc": "Release Date", "type": "lineedit"},

            # --- Theme Tags ---
            "[THEME_BG_GRADIENT_START]": {
                "desc": "Background Gradient Start",
                "type": "combobox", "editable": True,
                "options": ["#E0E0E0", "#FFFFFF", "#DDEEFF"]
            },
            "[THEME_BG_GRADIENT_END]": {
                "desc": "Background Gradient End",
                "type": "combobox", "editable": True,
                "options": ["#919191", "#AAAAAA", "#99AACC"]
            },
            "[THEME_PRIMARY_COLOR]": {
                "desc": "Primary Accent Color",
                "type": "combobox", "editable": True,
                "options": ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f1c40f"]
            },
            "[THEME_H1_COLOR]": {
                "desc": "Main Title (H1) Color",
                "type": "combobox", "editable": True,
                "options": ["#f8f8f8", "#ffffff", "#dddddd"]
            },
            "[THEME_FONT_BODY]": {
                "desc": "Body Font",
                "type": "combobox", "editable": True,
                "options": ["'Trueno', sans-serif", "'Arial', sans-serif", "'Verdana', sans-serif"]
            }
            ,
            # Additional theme-related, CSS tweakable tags
            "[THEME_FONT_SIZE_BODY]": {"desc": "Body font-size (e.g. 14px)", "type": "lineedit"},
            "[THEME_FONT_SIZE_H1]": {"desc": "H1 font-size (e.g. 37px)", "type": "lineedit"},
            "[THEME_H1_SHADOW_COLOR]": {"desc": "H1 shadow color (hex)", "type": "combobox", "editable": True, "options": ["#919191", "#b0b0b0", "#666666"]},
            "[THEME_H1_SHADOW_STRONG]": {"desc": "H1 strong shadow color (rgba)", "type": "combobox", "editable": True, "options": ["rgba(16,16,16,0.6)", "rgba(0,0,0,0.6)"]},
            "[THEME_H1_TRANSITION]": {"desc": "H1 transition (e.g. .3s)", "type": "lineedit"},
            "[THEME_DIV_BG]": {"desc": "Inner div background (color or gradient)", "type": "lineedit"},
            "[THEME_DIV_PADDING]": {"desc": "Inner div padding (e.g. 1em)", "type": "lineedit"},
            "[THEME_DIV_BORDER_RADIUS]": {"desc": "Inner div border-radius (e.g. 4px)", "type": "lineedit"},
            "[THEME_DIV_BOX_SHADOW]": {"desc": "Inner div box-shadow", "type": "lineedit"},
            "[THEME_LINK_COLOR]": {"desc": "Link accent color", "type": "combobox", "editable": True, "options": ["#3498db", "#2ecc71", "#e74c3c"]}
        }

        # Ensure every known tag has a 'default' value; default to the tag itself
        for k, v in self.known_tags.items():
            if 'default' not in v:
                v['default'] = k

        # Load defaults from site/index.set (hardcoded site defaults)
        self.site_defaults = self.load_site_defaults()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Top controls
        top_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to .set template file...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_template)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_template)
        # Button to reset fields to the site's hardcoded defaults
        self.load_defaults_btn = QPushButton("Load defaults")
        self.load_defaults_btn.clicked.connect(self.reset_to_site_defaults)

        top_layout.addWidget(self.path_edit)
        top_layout.addWidget(browse_btn)
        top_layout.addWidget(load_btn)
        top_layout.addWidget(self.load_defaults_btn)
        layout.addLayout(top_layout)

        # Scroll area for tags
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QVBoxLayout(self.scroll_content)
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        # Bottom controls
        bottom_layout = QHBoxLayout()
        save_btn = QPushButton("Generate HTML")
        save_btn.clicked.connect(self.generate_html)
        bottom_layout.addStretch()
        bottom_layout.addWidget(save_btn)
        layout.addLayout(bottom_layout)

        # Populate initial fields for known tags and theme tags using site defaults
        self.populate_initial_fields()

    def browse_template(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Template", "", "Set Files (*.set);;HTML Files (*.html);;All Files (*)")
        if fname:
            self.path_edit.setText(fname)
            self.load_template()

    def load_site_defaults(self):
        """Parse `site/index.set` for hardcoded theme defaults.

        Returns a dict mapping tag strings (e.g. '[THEME_BG_GRADIENT_START]')
        to values like '#E0E0E0'. If parsing fails for a variable, it is
        omitted from the returned dict.
        """
        defaults = {}
        try:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            site_path = os.path.normpath(os.path.join(base, 'site', 'index.set'))
            if not os.path.exists(site_path):
                return defaults
            with open(site_path, 'r', encoding='utf-8') as f:
                txt = f.read()

            # helper to try css var first, then fallbacks in the CSS
            def find_var(varname, fallback_regexes):
                # try CSS variable assignment
                m = re.search(rf"--{re.escape(varname)}\s*:\s*([^;]+);", txt)
                if m:
                    return m.group(1).strip()
                # try fallback regexes
                for rx in fallback_regexes:
                    m = re.search(rx, txt, re.IGNORECASE)
                    if m:
                        return m.group(1).strip()
                return None

            # Background gradient start/end
            g0 = find_var('theme-bg-gradient-start', [r"color-stop\(0%\s*,\s*([^,)\s]+)", r"startColorstr='([^']+)'"])
            g1 = find_var('theme-bg-gradient-end', [r"color-stop\(100%\s*,\s*([^,)\s]+)", r"endColorstr='([^']+)'"])
            if g0:
                defaults['[THEME_BG_GRADIENT_START]'] = g0
            if g1:
                defaults['[THEME_BG_GRADIENT_END]'] = g1

            # Primary color (loader border-top)
            p = find_var('theme-primary-color', [r"border-top:\s*\d+px\s+solid\s*([^;\s]+)"])
            if p:
                defaults['[THEME_PRIMARY_COLOR]'] = p

            # H1 color
            h1c = find_var('theme-h1-color', [r"h1\s*\{[^}]*color:\s*([^;]+);"])
            if h1c:
                defaults['[THEME_H1_COLOR]'] = h1c

            # Body font-family
            fbody = find_var('theme-font-body', [r"body\s*\{[^}]*font-family:\s*([^;]+);"])
            if fbody:
                defaults['[THEME_FONT_BODY]'] = fbody

            # Additional properties: sizes, div properties
            fsize_body = re.search(r"body\s*\{[^}]*font-size:\s*([^;]+);", txt, re.IGNORECASE)
            if fsize_body:
                defaults['[THEME_FONT_SIZE_BODY]'] = fsize_body.group(1).strip()
            fsize_h1 = re.search(r"h1\s*\{[^}]*font-size:\s*([^;]+);", txt, re.IGNORECASE)
            if fsize_h1:
                defaults['[THEME_FONT_SIZE_H1]'] = fsize_h1.group(1).strip()

            # inner div properties (#inner)
            inner = re.search(r"#inner\s*\{([^}]*)\}", txt, re.IGNORECASE | re.DOTALL)
            if inner:
                inner_css = inner.group(1)
                m = re.search(r"padding[-:\s]*([^;]+);", inner_css)
                if m:
                    defaults['[THEME_DIV_PADDING]'] = m.group(1).strip()
                m = re.search(r"border-radius[-:\s]*([^;]+);", inner_css)
                if m:
                    defaults['[THEME_DIV_BORDER_RADIUS]'] = m.group(1).strip()
                m = re.search(r"box-shadow[-:\s]*([^;]+);", inner_css)
                if m:
                    defaults['[THEME_DIV_BOX_SHADOW]'] = m.group(1).strip()

            # link color from a:hover / a
            m = re.search(r"a\s*\{[^}]*color:\s*([^;]+);", txt, re.IGNORECASE)
            if m:
                defaults['[THEME_LINK_COLOR]'] = m.group(1).strip()

        except Exception:
            return defaults

        return defaults

    def load_template(self):
        path = self.path_edit.text()
        if not os.path.exists(path):
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.template_content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file: {e}")
            return

        # Clear existing fields
        for i in reversed(range(self.form_layout.count())):
            self.form_layout.itemAt(i).widget().setParent(None)
        self.tag_widgets.clear()

        # Find tags that match known tags (whitelist). This avoids matching
        # arbitrary bracketed strings from JS/HTML that aren't variables.
        all_bracketed = set(re.findall(r'\[([^\]]+)\]', self.template_content))
        found_tags = {t for t in all_bracketed if f"[{t}]" in self.known_tags}

        # Sort alphabetically
        sorted_tags = sorted(list(found_tags))

        for tag_inner in sorted_tags:
            tag_full = f"[{tag_inner}]"
            
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 5, 0, 5)
            
            tag_info = self.known_tags.get(tag_full, {})
            label_text = tag_info.get("desc", tag_full)
            widget_type = tag_info.get("type", "lineedit")

            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold;")
            
            edit = None
            if widget_type == "textarea":
                edit = QTextEdit()
                edit.setPlaceholderText(f"Value for {tag_full}")
                edit.setAcceptRichText(False)
                edit.setMinimumHeight(80)
            elif widget_type == "combobox":
                edit = QComboBox()
                edit.setPlaceholderText(f"Value for {tag_full}")
                if tag_info.get("editable", False):
                    edit.setEditable(True)
                edit.addItems(tag_info.get("options", []))
            else: # lineedit
                edit = QLineEdit()
                edit.setPlaceholderText(f"Value for {tag_full}")
            # Pre-populate widgets with the tag text itself as a visible default
            # so users can see/keep the placeholder value easily.
            try:
                if isinstance(edit, QLineEdit):
                    edit.setText(tag_full)
                elif isinstance(edit, QTextEdit):
                    edit.setPlainText(tag_full)
                elif isinstance(edit, QComboBox):
                    # setCurrentText will work for editable combos
                    edit.setCurrentText(tag_full)
            except Exception:
                pass
            row_layout.addWidget(label)
            row_layout.addWidget(edit)
            
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            
            self.form_layout.addWidget(row_widget)
            self.form_layout.addWidget(line)
            
            self.tag_widgets[tag_full] = edit

        # If the "Load defaults" checkbox is enabled, populate widgets
        if hasattr(self, 'load_defaults_cb') and self.load_defaults_cb.isChecked():
            self.apply_defaults()

    def generate_html(self):
        if not self.template_content:
            return

        output_content = self.template_content
        # If the 'Load defaults' checkbox is checked, prefer known defaults
        # (or first combobox option) when the user left the field as the tag
        # placeholder. This produces a hardcoded HTML with concrete values.
        if hasattr(self, 'load_defaults_cb') and self.load_defaults_cb.isChecked():
            # build a replacement map taking widget values unless they
            # equal the literal tag (or are empty) in which case use
            # the declared default or first option
            replacements = {}
            for tag, widget in self.tag_widgets.items():
                tag_info = self.known_tags.get(tag, {})
                preferred = tag_info.get('default')
                # if default is the literal tag, try combobox options
                if preferred == tag:
                    if tag_info.get('type') == 'combobox':
                        opts = tag_info.get('options', [])
                        preferred = opts[0] if opts else ''
                    else:
                        preferred = ''

                # read widget current value
                value = ''
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QTextEdit):
                    value = widget.toPlainText()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()

                # If value is empty or still the literal tag, use preferred
                if not value or value == tag:
                    replacements[tag] = preferred
                else:
                    replacements[tag] = value

            for tag, value in replacements.items():
                output_content = output_content.replace(tag, value)
        else:
            for tag, widget in self.tag_widgets.items():
                value = ""
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QTextEdit):
                    value = widget.toPlainText()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                output_content = output_content.replace(tag, value)

        save_path, _ = QFileDialog.getSaveFileName(self, "Save HTML", "", "HTML Files (*.html)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                QMessageBox.information(self, "Success", "HTML generated successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def apply_defaults(self):
        """Populate form widgets from self.known_tags defaults/options.

        Only fills widgets that are currently empty to avoid overwriting user input.
        """
        for tag, widget in self.tag_widgets.items():
            tag_info = self.known_tags.get(tag, {})
            default_val = tag_info.get('default')

            # If no explicit default, try first option for combo boxes
            if default_val is None and tag_info.get('type') == 'combobox':
                opts = tag_info.get('options', [])
                if opts:
                    default_val = opts[0]

            if default_val is None:
                # leave blank if no reasonable default
                continue

            # Only set if widget is empty
            try:
                if isinstance(widget, QLineEdit) and not widget.text():
                    widget.setText(default_val)
                elif isinstance(widget, QTextEdit) and not widget.toPlainText():
                    widget.setPlainText(default_val)
                elif isinstance(widget, QComboBox) and not widget.currentText():
                    # setCurrentText works for editable and non-editable combos
                    widget.setCurrentText(default_val)
            except Exception:
                # be tolerant of any widget-setting problems
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiteGenerator()
    window.show()
    sys.exit(app.exec())