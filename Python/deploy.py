#!/usr/bin/env python3
"""deploy.py

Simple deploy UI to set values for a fixed list of bracketed tags
and write README.md and site/index.html with replacements.

Usage:
  python -m Python.deploy         # start GUI
  python -m Python.deploy --init-ini   # create deploy_ui.ini with keys
  python -m Python.deploy --apply      # apply values from INI and write outputs
"""

from pathlib import Path
import sys
import configparser
from typing import Dict
import tkinter as tk
import tkinter.messagebox



DEFAULT_INI = 'deploy_ui.ini'

# Fixed tags and their UI labels
FIXED_TAGS = [
    '-|-', 'CURV', 'GITUSER', 'GIT_SRC', 'GIT_WEB', 'PAYPAL', 'PORTABLE',
    'RDATE', 'RELEASEPG', 'REVISION', 'RJ_PROJ', 'RSHA1', 'RSIZE',
    'TAGLINE', 'VERSION'
]

LABELS = {
    '-|-': 'HTML Project Name',
    'CURV': 'Current Version',
    'GITUSER': 'GitHub UserName',
    'GIT_SRC': 'GitHub Source URL',
    'GIT_WEB': 'GitHub Website',
    'PAYPAL': 'PayPal Donate Link',
    'PORTABLE': 'Portable Compressed Binary URL',
    'RDATE': 'Release Date',
    'RELEASEPG': 'GitHub Releases Page',
    'REVISION': 'Current Installer Revision',
    'RJ_PROJ': 'Project Name',
    'RSHA1': 'Installer SHA Hash',
    'RSIZE': 'Installer Size',
    'TAGLINE': 'Tagline',
    'VERSION': 'Version'
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def load_ini(path: Path) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(path, encoding='utf-8')
    if 'values' not in cfg:
        cfg['values'] = {}
    # Ensure all keys exist (empty by default)
    for k in FIXED_TAGS:
        cfg['values'].setdefault(k, '')
    return cfg


def save_ini(path: Path, cfg: configparser.ConfigParser) -> None:
    with path.open('w', encoding='utf-8') as f:
        cfg.write(f)


def apply_replacements(values: Dict[str, str]) -> None:
    root = Path.cwd()
    readme_set = root / 'README.set'
    readme_md = root / 'README.md'
    site_set = root / 'site' / 'index.set'
    site_html = root / 'site' / 'index.html'

    def replace_in_file(in_path: Path, out_path: Path):
        if not in_path.exists():
            return
        txt = in_path.read_text(encoding='utf-8')
        for k, v in values.items():
            if not v:
                continue
            txt = txt.replace(f'[{k}]', v)
        out_path.write_text(txt, encoding='utf-8')

    replace_in_file(readme_set, readme_md)
    replace_in_file(site_set, site_html)


def init_ini(path: Path) -> None:
    cfg = configparser.ConfigParser()
    cfg['values'] = {k: '' for k in FIXED_TAGS}
    save_ini(path, cfg)


def run_cli_apply(ini_path: Path) -> None:
    cfg = load_ini(ini_path)
    values = {k: cfg['values'].get(k, '') for k in FIXED_TAGS}
    apply_replacements(values)
    print('Applied values and wrote README.md and site/index.html')


def run_gui(ini_path: Path) -> None:
    try:
        import tkinter as tk
        from tkinter import ttk
        import tkinter.font as tkfont
    except Exception:
        print('Tkinter not available; use --apply or --init-ini instead')
        sys.exit(1)

    cfg = load_ini(ini_path)

    root = tk.Tk()
    root.title('Deploy UI')

    bold_font = None
    try:
        bold_font = tkfont.Font(root=root, weight='bold')
    except Exception:
        bold_font = None

    entries = {}

    frm = ttk.Frame(root, padding=6)
    frm.pack(fill='both', expand=True)

    # Use grid: label in column 0, entry in column 1 (expand)
    frm.columnconfigure(1, weight=1)
    for row, tag in enumerate(FIXED_TAGS):
        label_text = LABELS.get(tag, tag)
        lbl = ttk.Label(frm, text=label_text)
        if bold_font:
            lbl.configure(font=bold_font)
        # minimal vertical spacing to reduce UI height
        lbl.grid(row=row, column=0, sticky='w', padx=(0, 8), pady=(2, 2))

        val = cfg['values'].get(tag, '')
        if not val:
            val = f'[{tag}]'
        ent = ttk.Entry(frm)
        ent.insert(0, val)
        ent.grid(row=row, column=1, sticky='ew', pady=(2, 2))
        entries[tag] = ent

    def save_all():
        for k, ent in entries.items():
            v = ent.get().strip()
            # Do not persist placeholder text like [TAG]
            if v == f'[{k}]':
                v = ''
            cfg['values'][k] = v
        save_ini(ini_path, cfg)

    def on_apply():
        save_all()
        values = {k: cfg['values'].get(k, '') for k in FIXED_TAGS}
        apply_replacements(values)
        tk.messagebox.showinfo('Deploy', 'Wrote README.md and site/index.html')

    btn_frm = ttk.Frame(root, padding=(0, 8))
    btn_frm.pack(fill='x')
    apply_btn = ttk.Button(btn_frm, text='Apply & Save', command=on_apply)
    apply_btn.pack(side='left')

    def on_close():
        save_all()
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    ini_path = Path(DEFAULT_INI)
    if '--init-ini' in argv:
        init_ini(ini_path)
        print(f'Created {ini_path}')
        return
    if '--apply' in argv:
        if not ini_path.exists():
            print('INI not found. Run with --init-ini or start the GUI to create it.')
            sys.exit(1)
        run_cli_apply(ini_path)
        return
    # Default: GUI
    if not ini_path.exists():
        init_ini(ini_path)
    run_gui(ini_path)


if __name__ == '__main__':
    main()
