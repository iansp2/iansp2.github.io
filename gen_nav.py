#!/usr/bin/env python3
"""Generate the `nav` block for zensical.toml from the docs/ tree.

Conventions this encodes:
  * Top-level order follows folder names, so keep your numeric prefixes
    ("1. HTB boxes"). The prefix is stripped from the *displayed* title,
    so the sidebar reads "HTB boxes", not "1. HTB boxes".
  * The site landing page (root index.md) is pinned to the very top and
    listed as a bare path, so Zensical takes its title from the page's own
    heading (e.g. "CTF Writeups"). index.md / README.md anywhere are always
    listed bare so they keep their in-page title.
  * The Daily Brief folder is special-cased: flat files named
    YYYY-MM-DD.md are grouped by month and shown newest-first
    (reverse chronological), which also collapses the long list.
  * Any folder named in IGNORE_DIRS (e.g. "assets") is skipped entirely.

Run:  python gen_nav.py          # prints the nav block to stdout
"""
from pathlib import Path
import re

DOCS = Path("docs")
DAILY_BRIEF_DIR = "0. Daily Brief"        # folder to reverse + group by month
IGNORE_DIRS = {"assets"}                  # folder names to leave out of the nav
INDEX_NAMES = {"index.md", "readme.md"}   # listed bare -> title comes from the page
PREFIX = re.compile(r"^\d+[.\-]?\s*")     # strips "0. ", "12-", "3 " ...

def title_of(name: str) -> str:
    stem = name[:-3] if name.endswith(".md") else name
    return PREFIX.sub("", stem).strip() or stem

def file_node(p: Path):
    """A page: bare string (auto title) for index/README, else an explicit title."""
    rel = str(p.relative_to(DOCS))
    if p.name.lower() in INDEX_NAMES:
        return rel
    return (title_of(p.name), rel)

def children(path: Path):
    for c in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        if c.name.startswith(".") or c.name in IGNORE_DIRS:
            continue
        yield c

def section_for(d: Path):
    if d.name == DAILY_BRIEF_DIR:
        return (title_of(d.name), build_daily_brief(d))
    return (title_of(d.name), build_section(d))

def build_section(path: Path, is_root: bool = False):
    dirs = [c for c in children(path) if c.is_dir()]
    files = [c for c in children(path) if c.is_file() and c.suffix == ".md"]

    if is_root:
        # root pages first (index.md pinned to the very top), then the folders
        files.sort(key=lambda p: (p.name.lower() not in INDEX_NAMES, p.name.lower()))
        return [file_node(f) for f in files] + [section_for(d) for d in dirs]

    # non-root: keep filesystem order, interleaving files and folders
    items = []
    for c in children(path):
        if c.is_dir():
            items.append(section_for(c))
        elif c.suffix == ".md":
            items.append(file_node(c))
    return items

def build_daily_brief(path: Path):
    dated, extras = [], []
    for md in path.glob("*.md"):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", md.stem)
        (dated if m else extras).append((md, m))
    # non-dated pages (index.md landing, etc.) stay at the top
    items = [file_node(p) for p, _ in sorted(extras, key=lambda t: t[0].name)]
    months: dict[str, list[Path]] = {}
    for md, m in dated:
        months.setdefault(f"{m.group(1)}-{m.group(2)}", []).append(md)
    for month in sorted(months, reverse=True):                      # newest month first
        days = sorted(months[month], key=lambda p: p.stem, reverse=True)  # newest day first
        # label each day with its full ISO date (change to d.stem[-2:] for day-only)
        items.append((month, [(d.stem[-2:], str(d.relative_to(DOCS))) for d in days]))
    return items

def emit(items, indent=1):
    pad = "  " * indent
    out = []
    for node in items:
        if isinstance(node, str):                       # bare page -> auto title
            out.append(f'{pad}"{node}",')
            continue
        title, value = node
        if isinstance(value, str):                      # titled page
            out.append(f'{pad}{{ "{title}" = "{value}" }},')
        else:                                           # section
            out.append(f'{pad}{{ "{title}" = [')
            out.extend(emit(value, indent + 1))
            out.append(f'{pad}] }},')
    return out

if __name__ == "__main__":
    print("nav = [")
    print("\n".join(emit(build_section(DOCS, is_root=True))))
    print("]")
