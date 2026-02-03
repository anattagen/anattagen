#!/usr/bin/env python3
"""deploy.py

Tool to load bracketed tags from README.set and site/index.set,
provide a simple UI to set values, save them to an INI file, and
write README.md and site/index.html with tags replaced.

Usage:
  python -m Python.deploy       # start GUI
  python -m Python.deploy --apply  # apply replacements using INI values
  python -m Python.deploy --init-ini  # create ini with keys discovered
"""
from __future__ import annotations

import configparser
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

DEFAULT_INI = "deploy_ui.ini"
README_SET = Path("README.set")
SITE_SET = Path("site") / "index.set"
OUT_README = Path("README.md")
OUT_INDEX = Path("site") / "index.html"

# Variables to exclude from the deploy UI
EXCLUDED_TAGS = {
    "0",
    "1",
    "?&",
    "htmlinjection",
    "just after lauch &amp; just before exit",
    "keymappers",
    "monitors",
    '^"&?\\/',
    "^\\/",
    "assigned level",
    '"module", "exports"',
    "data-smoothie",
    "i",
    "r",
    "t",
    "user",
    "pre / post",
}


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def find_tags_in_text(text: str) -> Set[str]:
    # Find bracketed tokens like [TAG]
    tokens = re.findall(r"\[([^\]]+)\]", text)
    return set(token.strip() for token in tokens)


def find_tags(files: List[Path]) -> List[str]:
    tags: Set[str] = set()
    for p in files:
        tags.update(find_tags_in_text(read_file(p)))
    # Filter out excluded tags (case-insensitive)
    excluded_lower = {tag.lower() for tag in EXCLUDED_TAGS}
    tags = {tag for tag in tags if tag.lower() not in excluded_lower}
    # Keep deterministic order
    return sorted(tags)


def load_ini(path: Path, keys: List[str]) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(path, encoding="utf-8")
    if "values" not in cfg:
        cfg["values"] = {}
    # Ensure keys exist
    for k in keys:
        if k not in cfg["values"]:
            cfg["values"][k] = ""
    return cfg


def save_ini(path: Path, cfg: configparser.ConfigParser) -> None:
    with path.open("w", encoding="utf-8") as f:
        cfg.write(f)


def apply_replacements(tag_values: Dict[str, str]) -> None:
    # Replace in README.set -> README.md
    readme_text = read_file(README_SET)
    index_text = read_file(SITE_SET)
    for k, v in tag_values.items():
        readme_text = readme_text.replace(f"[{k}]", v)
        index_text = index_text.replace(f"[{k}]", v)

    # Ensure site dir exists
    OUT_README.write_text(readme_text, encoding="utf-8")
    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_INDEX.write_text(index_text, encoding="utf-8")


def init_ini(ini_path: Path, keys: List[str]) -> None:
    cfg = load_ini(ini_path, keys)
    save_ini(ini_path, cfg)
    print(f"Created/updated INI: {ini_path}")


def run_cli_apply(ini_path: Path) -> None:
    cfg = configparser.ConfigParser()
    cfg.read(ini_path, encoding="utf-8")
    values = dict(cfg.get("values", fallback={})) if cfg else {}
    # Fallback: gather tags if none in ini
    tags = find_tags([README_SET, SITE_SET])
    tag_values = {k: values.get(k, "") for k in tags}
    apply_replacements(tag_values)
    print(f"Wrote {OUT_README} and {OUT_INDEX}")


def run_gui(ini_path: Path) -> None:
    try:
        import tkinter as tk
        from tkinter import ttk
        from tkinter import filedialog
    except Exception as e:
        print("Tkinter not available:", e)
        print("Use --apply or --init-ini instead.")
        sys.exit(1)

    tags = find_tags([README_SET, SITE_SET])
    cfg = load_ini(ini_path, tags)

    root = tk.Tk()
    root.title("Deploy: tag editor & builder")

    frame = ttk.Frame(root, padding=10)
    frame.grid(row=0, column=0, sticky="nsew")

    vars: Dict[str, tk.StringVar] = {}

    def save_all(_=None):
        for k, sv in vars.items():
            cfg["values"][k] = sv.get()
        save_ini(ini_path, cfg)
        apply_replacements({k: cfg["values"].get(k, "") for k in tags})

    # Build form
    for i, k in enumerate(tags):
        lbl = ttk.Label(frame, text=k)
        lbl.grid(row=i, column=0, sticky="w", padx=(0, 8), pady=4)
        sv = tk.StringVar(value=cfg["values"].get(k, ""))
        ent = ttk.Entry(frame, textvariable=sv, width=60)
        ent.grid(row=i, column=1, sticky="we", pady=4)
        vars[k] = sv

        # autosave on change
        def make_callback(key):
            def cb(*args):
                cfg["values"][key] = vars[key].get()
                save_ini(ini_path, cfg)
                apply_replacements({k: cfg["values"].get(k, "") for k in tags})
            return cb

        sv.trace_add("write", make_callback(k))

    # --- Build Section ---
    last_row = len(tags)
    ttk.Separator(frame, orient='horizontal').grid(row=last_row, column=0, columnspan=2, sticky="ew", pady=15)
    
    lbl_build = ttk.Label(frame, text="Build Portable Binary", font=("", 10, "bold"))
    lbl_build.grid(row=last_row+1, column=0, columnspan=2, pady=(0, 5))
    
    build_vars = {
        'onefile': tk.BooleanVar(value=False),
        'dest': tk.StringVar(value=str(Path("dist").absolute()))
    }
    
    ctl_frame = ttk.Frame(frame)
    ctl_frame.grid(row=last_row+2, column=0, columnspan=2, sticky="ew")
    
    ttk.Checkbutton(ctl_frame, text="Onefile", variable=build_vars['onefile']).pack(side="left", padx=5)
    ttk.Label(ctl_frame, text="Dest:").pack(side="left", padx=5)
    ttk.Entry(ctl_frame, textvariable=build_vars['dest']).pack(side="left", fill="x", expand=True)
    
    def browse_dest():
        d = filedialog.askdirectory()
        if d: build_vars['dest'].set(d)
    ttk.Button(ctl_frame, text="...", width=3, command=browse_dest).pack(side="left", padx=2)
    
    from tkinter import scrolledtext
    log_widget = scrolledtext.ScrolledText(frame, height=8, state='disabled', font=("Consolas", 8))
    log_widget.grid(row=last_row+3, column=0, columnspan=2, sticky="nsew", pady=5)
    
    def log(msg):
        def _log():
            log_widget.config(state='normal')
            log_widget.insert("end", msg)
            log_widget.see("end")
            log_widget.config(state='disabled')
        root.after(0, _log)

    def run_build():
        import threading
        import subprocess
        import platform
        
        onefile = build_vars['onefile'].get()
        dest = build_vars['dest'].get()
        
        def worker():
            sep = ';' if platform.system() == 'Windows' else ':'
            script_dir = Path(__file__).parent.absolute()
            project_root = script_dir.parent if script_dir.name == "Python" else script_dir
            main_script = project_root / "Python" / "main.py"
            icon_path = project_root / "assets" / "Joystick.ico"
            
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                str(main_script),
                '--name=anattagen',
                '--noconfirm',
                '--clean',
                '--windowed',
                f'--distpath={dest}',
                f'--add-data={project_root / "site"}{sep}site',
                f'--add-data={project_root / "assets"}{sep}assets',
            ]
            
            if platform.system() == 'Windows' and icon_path.exists():
                cmd.append(f'--icon={icon_path}')
            if onefile:
                cmd.append('--onefile')
            else:
                cmd.append('--onedir')
                
            log(f"Starting build...\nCommand: {' '.join(cmd)}\n")
            
            try:
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, encoding='utf-8', cwd=str(project_root)
                )
                for line in process.stdout:
                    log(line)
                process.wait()
                if process.returncode == 0:
                    log("\nBuild SUCCESS!\n")
                else:
                    log(f"\nBuild FAILED with code {process.returncode}\n")
            except Exception as e:
                log(f"\nError: {e}\n")
                
        threading.Thread(target=worker, daemon=True).start()

    ttk.Button(frame, text="Compile", command=run_build).grid(row=last_row+4, column=0, columnspan=2, pady=10)

    # Buttons
    btn_frame = ttk.Frame(root, padding=(10, 6))
    btn_frame.grid(row=1, column=0, sticky="ew")
    apply_btn = ttk.Button(btn_frame, text="Apply & Save", command=save_all)
    apply_btn.pack(side="left")

    def on_close():
        save_all()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


def main(argv: List[str]) -> None:
    ini_path = Path(DEFAULT_INI)
    if "--init-ini" in argv:
        tags = find_tags([README_SET, SITE_SET])
        init_ini(ini_path, tags)
        return
    if "--apply" in argv:
        if not ini_path.exists():
            print("INI not found. Run with --init-ini or start the GUI to create it.")
            sys.exit(1)
        run_cli_apply(ini_path)
        return
    # Default: start GUI
    if not ini_path.exists():
        tags = find_tags([README_SET, SITE_SET])
        init_ini(ini_path, tags)
    run_gui(ini_path)


if __name__ == "__main__":
    main(sys.argv[1:])
