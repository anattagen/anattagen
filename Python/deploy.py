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
    except Exception as e:
        print("Tkinter not available:", e)
        print("Use --apply or --init-ini instead.")
        sys.exit(1)

    tags = find_tags([README_SET, SITE_SET])
    cfg = load_ini(ini_path, tags)

    root = tk.Tk()
    root.title("Deploy: tag editor")

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
import os
import re
import fnmatch
import configparser
from pathlib import Path
import argparse
from typing import Set


ROOT = Path(__file__).resolve().parent.parent


def load_gitignore(path: Path):
    gitignore = path / '.gitignore'
    patterns = []
    if not gitignore.exists():
        return patterns
    for line in gitignore.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        patterns.append(line)
    return patterns


def is_ignored(rel_path: str, patterns):
    # rel_path uses forward slashes
    for pat in patterns:
        p = pat.strip()
        if not p:
            continue
        # Normalize patterns and test with fnmatch first
        try:
            if fnmatch.fnmatch(rel_path, p):
                return True
        except Exception:
            pass
        # Directory pattern like "dir/" -> match prefix
        if p.endswith('/'):
            prefix = p.rstrip('/')
            if rel_path == prefix or rel_path.startswith(prefix + '/'):
                return True
        # Pattern with trailing /* -> match directory prefix
        if p.endswith('/*'):
            prefix = p[:-2]
            if rel_path == prefix or rel_path.startswith(prefix + '/'):
                return True
    return False


def render_tree(root: Path, patterns):
    lines = []
    def walk(dir_path: Path, prefix=''):
        entries = sorted([p for p in dir_path.iterdir()])
        # filter ignored entries first so last-item detection is correct
        visible = [p for p in entries if not is_ignored(p.relative_to(ROOT).as_posix(), patterns)]
        for i, p in enumerate(visible):
            rel = p.relative_to(ROOT).as_posix()
            connector = '└──' if i == len(visible) - 1 else '├──'
            if p.is_dir():
                lines.append(f"{prefix}{connector} {p.name}/")
                extension = '    ' if i == len(visible) - 1 else '│   '
                walk(p, prefix + extension)
            else:
                lines.append(f"{prefix}{connector} {p.name}")
    # root
    lines.append(f"{ROOT.name}/")
    walk(ROOT)
    return '\n'.join(lines)


def load_ini_values(ini_path: Path):
    cfg = configparser.ConfigParser()
    if not ini_path.exists():
        return {}
    cfg.read(ini_path, encoding='utf-8')
    if 'values' in cfg:
        return dict(cfg['values'])
    return {}


def find_tags_in_text(text: str) -> Set[str]:
    # find tokens like [KEY]
    tags = set(re.findall(r"\[([A-Za-z0-9_\-]+)\]", text))
    # Filter out excluded tags
    tags = tags - EXCLUDED_TAGS
    return tags


def create_ini_from_template(ini_path: Path, template_path: Path):
    # If ini exists, do nothing
    if ini_path.exists():
        return False
    if not template_path.exists():
        # create empty ini
        cfg = configparser.ConfigParser()
        cfg['values'] = {}
        with ini_path.open('w', encoding='utf-8') as f:
            cfg.write(f)
        return True

    tpl = template_path.read_text(encoding='utf-8')
    tags = find_tags_in_text(tpl)
    cfg = configparser.ConfigParser()
    cfg['values'] = {}
    for t in sorted(tags):
        # default to the literal tag so replacement is a no-op until user edits
        cfg['values'][t] = f'[{t}]'
    with ini_path.open('w', encoding='utf-8') as f:
        cfg.write(f)
    return True


def replace_tags_in_text(text: str, values: dict):
    out = text
    for k, v in values.items():
        tag = f'[{k}]'
        out = out.replace(tag, v)
    return out


def update_readme_set(readme_set_path: Path, tree_text: str):
    txt = readme_set_path.read_text(encoding='utf-8')
    # Replace existing code block that starts with a line containing "anattagen/" under a code fence
    # We'll find the first triple-backtick block that contains "anattagen/" and replace its contents with the new tree
    lines = readme_set_path.read_text(encoding='utf-8').splitlines()
    # Find the line index that contains the repo root folder as the tree header (e.g., 'anattagen/')
    tree_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith(f"{ROOT.name}/"):
            tree_idx = i
            break

    if tree_idx is not None:
        # find preceding fence start (a line beginning with 3+ backticks)
        start = None
        for i in range(tree_idx, -1, -1):
            if re.match(r"^`{3,}", lines[i].strip()):
                start = i
                break
        # find fence end after tree_idx
        end = None
        for j in range(tree_idx, len(lines)):
            if re.match(r"^`{3,}", lines[j].strip()) and j != start:
                end = j
                break

        if start is not None and end is not None:
            new_block = ["```", tree_text, "```"]
            new_lines = lines[:start] + new_block + lines[end+1:]
            readme_set_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
            return True

    # Fallback: append a fenced block with the tree at the end
    with readme_set_path.open('a', encoding='utf-8') as f:
        f.write('\n```\n' + tree_text + '\n```\n')
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate README.md and site/index.html from templates')
    parser.add_argument('--init-ini', action='store_true', help='Create site_values.ini from site/index.set if missing')
    args = parser.parse_args()

    # Paths
    root = ROOT
    readme_set = root / 'README.set'
    readme_md = root / 'README.md'
    site_index_set = root / 'site' / 'index.set'
    site_index_html = root / 'site' / 'index.html'
    ini_path = root / 'site_values.ini'

    # Optionally initialize ini from template (does not modify README.set)
    if args.init_ini:
        created = create_ini_from_template(ini_path, site_index_set)
        if created:
            print(f'Created {ini_path}')

    # Load values from ini in project root
    values = load_ini_values(ini_path)

    # Replace tags in README.set and write README.md (do not change README.set itself)
    if readme_set.exists():
        input_text = readme_set.read_text(encoding='utf-8')
        out_text = replace_tags_in_text(input_text, values)
        readme_md.write_text(out_text, encoding='utf-8')

    # Replace tags in site/index.set and write site/index.html
    if site_index_set.exists():
        tpl = site_index_set.read_text(encoding='utf-8')
        out = replace_tags_in_text(tpl, values)
        site_index_html.write_text(out, encoding='utf-8')

    print('Updated README.md and site/index.html')


if __name__ == '__main__':
    main()
