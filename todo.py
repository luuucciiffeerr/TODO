#!/usr/bin/env python3
"""
todo — ultra-light personal CLI task manager with nested tags
Encrypted, per-user, cross-platform. Lives entirely in your terminal.
See: todo --help | https://github.com/luuucciiffeerr/todo
"""

__version__ = "1.0.0"

import argparse
import base64
import getpass
import hashlib
import json
import os
import platform
import re
import secrets
import sys
from datetime import date, datetime
from pathlib import Path

# ── Minimum Python version ────────────────────────────────────────────────────
if sys.version_info < (3, 8):
    sys.exit("todo requires Python 3.8 or newer.")

# ── Optional encryption (cryptography library) ───────────────────────────────
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ── Data directory (per-user, OS-appropriate) ────────────────────────────────

def get_data_dir() -> Path:
    """
    Returns the user-specific data directory for todo.
    - Linux/macOS: ~/.local/share/todo  (XDG_DATA_HOME respected)
    - Windows:     %APPDATA%\\todo
    Falls back to ~/.todo if neither is available.
    """
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif system in ("Linux", "Darwin"):
        xdg = os.environ.get("XDG_DATA_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    else:
        base = Path.home()

    data_dir = base / "todo"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        # Restrict permissions on Unix (owner read/write only)
        if system in ("Linux", "Darwin"):
            os.chmod(data_dir, 0o700)
    except OSError as e:
        # Fallback
        fallback = Path.home() / ".todo"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
    return data_dir


DATA_DIR  = get_data_dir()
DATA_FILE = DATA_DIR / "tasks.json"
SALT_FILE = DATA_DIR / ".salt"
LOCK_FILE = DATA_DIR / ".lock"

# ── ANSI colours ──────────────────────────────────────────────────────────────

def _ansi(*codes): return f"\033[{';'.join(str(c) for c in codes)}m"

RST     = _ansi(0)
BOLD    = _ansi(1)
DIM     = _ansi(2)
RED     = _ansi(91)
YELLOW  = _ansi(93)
GREEN   = _ansi(92)
CYAN    = _ansi(96)
MAGENTA = _ansi(95)
BG_SEL  = _ansi(48, 5, 236)
BG_TAG  = _ansi(48, 5, 17)

TAG_COLORS = [_ansi(96), _ansi(95), _ansi(93), _ansi(92), _ansi(94), _ansi(91)]

PRIORITY_COLOR = {"1": RED, "2": YELLOW, "3": ""}
PRIORITY_LABEL = {"1": "!", "2": "~", "3": " "}

# ── Encryption helpers ────────────────────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,   # NIST 2023 recommendation
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _get_or_create_salt() -> bytes:
    """Load existing salt or create a new cryptographically-random one."""
    if SALT_FILE.exists():
        return SALT_FILE.read_bytes()
    salt = secrets.token_bytes(32)
    SALT_FILE.write_bytes(salt)
    # Restrict to owner-read-only on Unix
    if platform.system() in ("Linux", "Darwin"):
        os.chmod(SALT_FILE, 0o400)
    return salt


def encrypt_data(data: str, password: str) -> bytes:
    salt = _get_or_create_salt()
    key  = _derive_key(password, salt)
    f    = Fernet(key)
    return f.encrypt(data.encode("utf-8"))


def decrypt_data(ciphertext: bytes, password: str) -> str:
    salt = _get_or_create_salt()
    key  = _derive_key(password, salt)
    f    = Fernet(key)
    return f.decrypt(ciphertext).decode("utf-8")


# ── Password / encryption workflow ───────────────────────────────────────────

def is_encrypted() -> bool:
    """Return True if the data file looks like Fernet ciphertext."""
    if not DATA_FILE.exists():
        return False
    raw = DATA_FILE.read_bytes()
    # Fernet tokens start with 'gAAAAA' in base64
    return raw[:6] == b"gAAAAA"


def prompt_password(confirm: bool = False) -> str:
    """Prompt for a password (twice if confirm=True)."""
    pw = getpass.getpass("  🔒 Password: ")
    if confirm:
        pw2 = getpass.getpass("  🔒 Confirm:  ")
        if pw != pw2:
            sys.exit("  ✗ Passwords do not match.")
    return pw


# ── Data model ────────────────────────────────────────────────────────────────

def empty_doc() -> dict:
    return {"tasks": [], "tags": [], "_version": __version__}


def empty_tag(name: str) -> dict:
    return {"type": "tag", "name": name, "tasks": [], "tags": []}


def empty_task(text: str, priority=None, due=None) -> dict:
    return {"type": "task", "text": text, "done": False,
            "priority": priority, "due": due,
            "created": date.today().isoformat()}


def load(password: str | None = None) -> dict:
    """Load and optionally decrypt the data file."""
    if not DATA_FILE.exists():
        return empty_doc()

    raw = DATA_FILE.read_bytes()

    if is_encrypted():
        if not HAS_CRYPTO:
            sys.exit(
                "  ✗ Data file is encrypted but 'cryptography' is not installed.\n"
                "    Run: pip install cryptography"
            )
        if password is None:
            password = prompt_password()
        try:
            raw = decrypt_data(raw, password).encode()
        except (InvalidToken, Exception):
            sys.exit("  ✗ Wrong password or corrupted data.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit("  ✗ Data file is corrupted. Backup at: " + str(DATA_FILE))

    # Migrate v1/v2 plain-list format
    if isinstance(data, list):
        doc = empty_doc()
        for item in data:
            if isinstance(item, str):
                doc["tasks"].append(empty_task(item))
            elif isinstance(item, dict) and item.get("type") != "tag":
                doc["tasks"].append({**empty_task(""), **item, "type": "task"})
        return doc

    return data


def save(doc: dict, password: str | None = None) -> None:
    """Serialize and optionally encrypt the data file (atomic write)."""
    raw = json.dumps(doc, ensure_ascii=False, indent=2)

    if password is not None and HAS_CRYPTO:
        content = encrypt_data(raw, password)
        write_bytes = True
    elif is_encrypted() and password is None:
        # Already encrypted, leave as-is (shouldn't reach here normally)
        return
    else:
        content = raw.encode("utf-8")
        write_bytes = True

    # Atomic write: write to temp then rename
    tmp = DATA_FILE.with_suffix(".tmp")
    try:
        if write_bytes:
            tmp.write_bytes(content if isinstance(content, bytes) else content)
        # Restrict file permissions on Unix
        if platform.system() in ("Linux", "Darwin"):
            os.chmod(tmp, 0o600)
        tmp.replace(DATA_FILE)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        sys.exit(f"  ✗ Could not save data: {e}")


# ── Parsing helpers ───────────────────────────────────────────────────────────

def parse_task_input(words: list) -> dict:
    priority = None; due = None; text_words = []
    for w in words:
        if re.fullmatch(r"![123]", w):
            priority = w[1]
        elif re.fullmatch(r"@\d{4}-\d{2}-\d{2}", w):
            due = w[1:]
        else:
            text_words.append(w)
    return empty_task(" ".join(text_words).strip(), priority, due)


def normalize_args(words: list) -> list:
    """Handle PowerShell quoting of #-tags."""
    if len(words) == 1:
        return words[0].split()
    return words


def extract_tags_and_text(words: list) -> tuple:
    """Return (tag_path: list[str], remaining_words: list[str])"""
    tags = []; rest = []
    for w in normalize_args(words):
        if w.startswith("#") and len(w) > 1:
            tags.append(w[1:].lower())
        else:
            rest.append(w)
    return tags, rest


def navigate_to_tag(doc: dict, path: list, create: bool = False):
    node = doc
    for name in path:
        found = next((t for t in node.get("tags", []) if t["name"] == name), None)
        if found is None:
            if create:
                new_tag = empty_tag(name)
                node.setdefault("tags", []).append(new_tag)
                node = new_tag
            else:
                return None
        else:
            node = found
    return node


def find_tag_by_number(doc: dict, n: int) -> tuple:
    counter = [0]
    def walk(node, parent):
        for tag in node.get("tags", []):
            counter[0] += 1
            if counter[0] == n:
                return tag, node
            result = walk(tag, tag)
            if result[0]: return result
        return None, None
    return walk(doc, doc)


# ── Due date display ──────────────────────────────────────────────────────────

def due_label(due_str) -> str:
    if not due_str: return ""
    try:
        d = datetime.strptime(due_str, "%Y-%m-%d").date()
        delta = (d - date.today()).days
        if delta < 0:    return f" {RED}[overdue {due_str}]{RST}"
        elif delta == 0: return f" {YELLOW}[today]{RST}"
        elif delta <= 3: return f" {YELLOW}[{due_str}]{RST}"
        else:            return f" {DIM}[{due_str}]{RST}"
    except ValueError:
        return f" [{due_str}]"


# ── Rendering ─────────────────────────────────────────────────────────────────

def task_line(num, t, width, indent=0, cursor=False, num_override=None) -> str:
    pad   = "  " * indent
    n     = (num_override or str(num)).rjust(width)
    check = f"{DIM}[x]{RST}" if t["done"] else "[ ]"
    pri   = t.get("priority")
    pc    = PRIORITY_COLOR.get(pri, "")
    pl    = PRIORITY_LABEL.get(pri, " ")
    text  = f"{DIM}{t['text']}{RST}" if t["done"] else f"{pc}{t['text']}{RST}"
    due   = due_label(t.get("due"))
    arrow = f"{GREEN}>{RST}" if cursor else " "
    bg    = BG_SEL if cursor else ""
    return f"{bg}{pad}  {arrow} {n}. {check} {pl} {text}{due}{RST}"


def tag_line(num, tag, width, indent=0, expanded=False, cursor=False,
             color_idx=0, task_count=0) -> str:
    pad   = "  " * indent
    n     = str(num).rjust(width)
    col   = TAG_COLORS[color_idx % len(TAG_COLORS)]
    arrow = "+" if expanded else ">"
    done_c = sum(1 for t in tag["tasks"] if t.get("done"))
    count = f"{DIM} ({done_c}/{task_count}){RST}" if task_count > 0 else f"{DIM} (empty){RST}"
    cur   = f"{GREEN}>{RST}" if cursor else " "
    bg    = BG_SEL if cursor else BG_TAG
    return f"{bg}{pad}  {cur} {col}{BOLD}#{tag['name']}{RST}{bg}{count}  {col}{arrow}{RST}{RST}"


def count_tasks_recursive(node: dict) -> int:
    total = len(node.get("tasks", []))
    for sub in node.get("tags", []):
        total += count_tasks_recursive(sub)
    return total


def build_render_list(doc, expanded_tags, indent=0, color_idx=0,
                      _tag_num=None, _task_num=None) -> list:
    if _tag_num is None:  _tag_num  = [0]
    if _task_num is None: _task_num = [0]
    rows = []
    for tag in doc.get("tags", []):
        _tag_num[0] += 1
        tag_id = id(tag)
        expanded = tag_id in expanded_tags
        tc = count_tasks_recursive(tag)
        rows.append({"kind": "tag", "node": tag, "parent": doc,
                     "num": _tag_num[0], "indent": indent,
                     "color_idx": color_idx, "expanded": expanded,
                     "task_count": tc})
        if expanded:
            sub = build_render_list(tag, expanded_tags,
                                    indent=indent+1, color_idx=color_idx+1,
                                    _tag_num=_tag_num, _task_num=_task_num)
            rows.extend(sub)
    for task in doc.get("tasks", []):
        _task_num[0] += 1
        rows.append({"kind": "task", "node": task, "parent": doc,
                     "num": _task_num[0], "indent": indent, "color_idx": color_idx})
    return rows


def print_doc(doc, expanded_tags=None, show_all=False) -> None:
    if expanded_tags is None:
        expanded_tags = set()
    if show_all:
        def all_ids(node):
            s = set()
            for t in node.get("tags", []):
                s.add(id(t)); s |= all_ids(t)
            return s
        expanded_tags = all_ids(doc)

    rows = build_render_list(doc, expanded_tags)
    if not rows:
        print(f"  {DIM}(nothing here — try: todo -a your first task){RST}")
        return

    tag_width  = max((len(str(r["num"])) for r in rows if r["kind"] == "tag"),  default=1)
    task_width = max((len(str(r["num"])) for r in rows if r["kind"] == "task"), default=1)

    for r in rows:
        if r["kind"] == "tag":
            print(tag_line(r["num"], r["node"], tag_width, r["indent"],
                           r["expanded"], False, r["color_idx"], r["task_count"]))
        else:
            print(task_line(r["num"], r["node"], task_width, r["indent"]))


# ── Interactive TUI ───────────────────────────────────────────────────────────

def interactive(doc: dict, password=None) -> None:
    system = platform.system()

    if system == "Windows":
        try:
            import msvcrt
        except ImportError:
            print("Interactive mode requires Windows msvcrt.", file=sys.stderr)
            sys.exit(1)

        def getch():
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                return ch + msvcrt.getwch()
            return ch

        UP = "\xe0H"; DOWN = "\xe0P"; RIGHT = "\xe0M"; LEFT = "\xe0K"
        CLEAR = "cls"

    else:
        import tty, termios

        def getch():
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        return "\x1b[" + ch3
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

        UP = "\x1b[A"; DOWN = "\x1b[B"; RIGHT = "\x1b[C"; LEFT = "\x1b[D"
        CLEAR = "clear"

    expanded = set()
    cursor = [0]

    def rows():
        return build_render_list(doc, expanded)

    def redraw(rs=None):
        if rs is None: rs = rows()
        os.system(CLEAR)
        if not rs:
            print(f"\n  {DIM}(nothing here){RST}\n")
        else:
            tw = max((len(str(r["num"])) for r in rs if r["kind"] == "tag"),  default=1)
            kw = max((len(str(r["num"])) for r in rs if r["kind"] == "task"), default=1)
            for i, r in enumerate(rs):
                is_cur = (i == cursor[0])
                if r["kind"] == "tag":
                    print(tag_line(r["num"], r["node"], tw, r["indent"],
                                   r["expanded"], is_cur, r["color_idx"], r["task_count"]))
                else:
                    print(task_line(r["num"], r["node"], kw, r["indent"], is_cur))
        print()
        print(f"  {BOLD}↑↓{RST} move  {BOLD}→{RST} expand  {BOLD}←{RST} collapse  "
              f"{BOLD}Space{RST} done  {BOLD}d{RST} delete  "
              f"{BOLD}a{RST} add  {BOLD}t{RST} new tag  "
              f"{BOLD}e{RST} edit  {BOLD}q{RST} quit")

    while True:
        rs = rows()
        if rs and cursor[0] >= len(rs): cursor[0] = len(rs) - 1
        if cursor[0] < 0: cursor[0] = 0
        redraw(rs)
        ch = getch()
        rs = rows()

        if ch == UP:
            if cursor[0] > 0: cursor[0] -= 1
        elif ch == DOWN:
            if cursor[0] < len(rs) - 1: cursor[0] += 1
        elif ch == RIGHT:
            if rs and cursor[0] < len(rs):
                r = rs[cursor[0]]
                if r["kind"] == "tag":
                    expanded.add(id(r["node"]))
        elif ch == LEFT:
            if rs and cursor[0] < len(rs):
                r = rs[cursor[0]]
                if r["kind"] == "tag" and id(r["node"]) in expanded:
                    expanded.discard(id(r["node"]))
                else:
                    target_indent = r["indent"] - 1
                    for j in range(cursor[0] - 1, -1, -1):
                        if rs[j]["indent"] == target_indent and rs[j]["kind"] == "tag":
                            expanded.discard(id(rs[j]["node"]))
                            cursor[0] = j
                            break
        elif ch == " ":
            if rs and cursor[0] < len(rs):
                r = rs[cursor[0]]
                if r["kind"] == "task":
                    r["node"]["done"] = not r["node"]["done"]
                    save(doc, password)
        elif ch in ("d", "D"):
            if rs and cursor[0] < len(rs):
                r = rs[cursor[0]]
                if r["kind"] == "task":
                    r["parent"]["tasks"].remove(r["node"])
                    save(doc, password)
                    if cursor[0] >= len(rows()) and cursor[0] > 0:
                        cursor[0] -= 1
                elif r["kind"] == "tag":
                    os.system(CLEAR)
                    tc = count_tasks_recursive(r["node"])
                    confirm = input(f"  Delete #{r['node']['name']} and {tc} task(s)? [y/N] ")
                    if confirm.lower() == "y":
                        r["parent"]["tags"].remove(r["node"])
                        expanded.discard(id(r["node"]))
                        save(doc, password)
                        if cursor[0] >= len(rows()) and cursor[0] > 0:
                            cursor[0] -= 1
        elif ch in ("a", "A"):
            parent_node = doc
            if rs and cursor[0] < len(rs):
                r = rs[cursor[0]]
                if r["kind"] == "tag" and id(r["node"]) in expanded:
                    parent_node = r["node"]
                elif r["indent"] > 0:
                    for j in range(cursor[0], -1, -1):
                        if rs[j]["kind"] == "tag" and rs[j]["indent"] == r["indent"] - 1:
                            parent_node = rs[j]["node"]
                            break
            os.system(CLEAR)
            ctx = f"#{parent_node['name']}" if parent_node.get("name") else "root"
            raw = input(f"  Add task [{ctx}] (!1/!2/!3 priority, @YYYY-MM-DD due): ").strip()
            if raw:
                words = raw.split()
                tag_path, rest = extract_tags_and_text(words)
                target = navigate_to_tag(parent_node, tag_path, create=True) if tag_path else parent_node
                t = parse_task_input(rest)
                if t["text"]:
                    target["tasks"].append(t)
                    save(doc, password)
        elif ch in ("t", "T"):
            os.system(CLEAR)
            name = input("  New tag name (a-z 0-9 _ -): ").strip().lower()
            if name and re.fullmatch(r"[a-z0-9_\-]+", name):
                parent_node = doc
                if rs and cursor[0] < len(rs):
                    r = rs[cursor[0]]
                    if r["kind"] == "tag" and id(r["node"]) in expanded:
                        parent_node = r["node"]
                existing = next((t for t in parent_node.get("tags", []) if t["name"] == name), None)
                if not existing:
                    parent_node.setdefault("tags", []).append(empty_tag(name))
                    save(doc, password)
            else:
                os.system(CLEAR)
                input("  Invalid tag name. Press Enter.")
        elif ch in ("e", "E"):
            if rs and cursor[0] < len(rs):
                r = rs[cursor[0]]
                if r["kind"] == "task":
                    os.system(CLEAR)
                    raw = input(f"  Edit [{r['node']['text']}]: ").strip()
                    if raw:
                        p = parse_task_input(raw.split())
                        if p["text"]:     r["node"]["text"]     = p["text"]
                        if p["priority"]: r["node"]["priority"] = p["priority"]
                        if p["due"]:      r["node"]["due"]      = p["due"]
                        save(doc, password)
                elif r["kind"] == "tag":
                    os.system(CLEAR)
                    name = input(f"  Rename tag [{r['node']['name']}]: ").strip().lower()
                    if name and re.fullmatch(r"[a-z0-9_\-]+", name):
                        r["node"]["name"] = name
                        save(doc, password)
        elif ch in ("q", "Q", "\x03", "\x04"):
            os.system(CLEAR)
            print_doc(doc, show_all=False)
            break


# ── Encryption management commands ───────────────────────────────────────────

def cmd_encrypt(doc: dict, password_arg=None) -> None:
    if not HAS_CRYPTO:
        sys.exit(
            "  ✗ Encryption requires the 'cryptography' package.\n"
            "    Install with: pip install cryptography"
        )
    if is_encrypted():
        print("  ✓ Data is already encrypted.")
        return
    pw = password_arg or prompt_password(confirm=True)
    save(doc, password=pw)
    print(f"  ✓ Data encrypted and saved to: {DATA_FILE}")
    print(f"  ⚠  Remember your password — there is no recovery without it.")


def cmd_decrypt(password_arg=None) -> None:
    if not is_encrypted():
        print("  Data is not encrypted.")
        return
    pw = password_arg or prompt_password()
    doc = load(password=pw)
    # Save without encryption
    raw = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_bytes(raw)
    if platform.system() in ("Linux", "Darwin"):
        os.chmod(tmp, 0o600)
    tmp.replace(DATA_FILE)
    print(f"  ✓ Data decrypted. File is now plain JSON at: {DATA_FILE}")


# ── Main ──────────────────────────────────────────────────────────────────────

HELP_TEXT = f"""\
{BOLD}todo{RST} v{__version__} — ultra-light personal CLI task manager

{BOLD}USAGE{RST}
  todo                          show tasks (tags collapsed)
  todo --all                    expand everything
  todo #work                    open tag by name
  todo #2                       open tag by number

{BOLD}ADDING{RST}
  todo -a fix the bug           add task to root
  todo -a #work fix bug         add to tag 'work' (creates if missing)
  todo -a #work #backend bug    nested tags (work > backend)
  todo -a !1 urgent thing       priority: !1=high  !2=med  !3=normal
  todo -a call dentist @2025-05-30   due date
  todo -a #work !1 @2025-05-30 deploy   all combined

{BOLD}MODIFYING{RST}
  todo -d 3                     toggle done on task #3
  todo -d #work 2               toggle done inside tag
  todo -e 2 new task text       edit task #2
  todo -m 2 up|down             reorder tasks

{BOLD}REMOVING{RST}
  todo -r 3                     remove task #3 from root
  todo -r #work 2               remove inside tag
  todo --rmtag #work            remove tag and everything inside
  todo --rmtag 2                remove tag by number

{BOLD}SEARCH & MISC{RST}
  todo -s keyword               search all tasks (across all tags)
  todo --clear                  wipe everything (asks confirmation)
  todo --version                print version

{BOLD}ENCRYPTION{RST}
  todo --encrypt                encrypt data file with a password
  todo --decrypt                remove encryption (requires password)
  Note: install 'cryptography' first:  pip install cryptography

{BOLD}INTERACTIVE TUI{RST}
  todo -i
    ↑↓       navigate    →  expand    ←  collapse
    Space    toggle done  d  delete    a  add task
    t        new tag      e  edit      q  quit

{BOLD}DATA LOCATION{RST}
  {DATA_FILE}

{BOLD}SYNTAX{RST}
  !1 !2 !3      priority (high / medium / normal)
  @YYYY-MM-DD   due date
  #tagname      tag  (chain for nesting: #work #backend)
"""


def main() -> None:
    # Enable ANSI on Windows
    if sys.platform == "win32":
        os.system("")

    parser = argparse.ArgumentParser(prog="todo", add_help=False)
    parser.add_argument("--help",        "-h",  action="store_true")
    parser.add_argument("--version",            action="store_true")
    parser.add_argument("--all",                action="store_true")
    parser.add_argument("--add",         "-a",  nargs="+", metavar="WORD")
    parser.add_argument("--rm",          "-r",  nargs="+", metavar="ARG")
    parser.add_argument("--rmtag",              nargs="+", metavar="ARG")
    parser.add_argument("--done",        "-d",  nargs="+", metavar="ARG")
    parser.add_argument("--edit",        "-e",  nargs="+", metavar="WORD")
    parser.add_argument("--move",        "-m",  nargs="+", metavar="ARG")
    parser.add_argument("--search",      "-s",  nargs="+", metavar="WORD")
    parser.add_argument("--clear",              action="store_true")
    parser.add_argument("--interactive", "-i",  action="store_true")
    parser.add_argument("--encrypt",            action="store_true")
    parser.add_argument("--decrypt",            action="store_true")
    parser.add_argument("--password",    "-p",  type=str, default=None,
                        help="password (use env var TODO_PASSWORD instead)")
    parser.add_argument("positional",           nargs="*")

    args = parser.parse_args()

    if args.help:
        print(HELP_TEXT); return

    if args.version:
        print(f"todo {__version__}"); return

    # Prefer environment variable for password (safer than CLI flag)
    password = os.environ.get("TODO_PASSWORD") or args.password

    # Load data (may prompt for password if encrypted)
    if args.encrypt:
        doc = load(password=password) if not is_encrypted() else None
        if doc is not None:
            cmd_encrypt(doc, password)
        return

    if args.decrypt:
        cmd_decrypt(password)
        return

    doc = load(password=password)

    # Determine effective password to use for subsequent saves
    # If file is currently encrypted but we loaded with a password, keep that password
    effective_pw = password if is_encrypted() or password else None

    # ── add ──────────────────────────────────────────────────────────────────
    if args.add:
        tag_path, rest = extract_tags_and_text(args.add)
        target = navigate_to_tag(doc, tag_path, create=True) if tag_path else doc
        t = parse_task_input(rest)
        if not t["text"]:
            print("Error: empty task text.", file=sys.stderr); sys.exit(1)
        target["tasks"].append(t)
        save(doc, effective_pw)
        ctx = " > ".join(f"#{p}" for p in tag_path) if tag_path else "root"
        print(f"Added to [{ctx}]: {t['text']}")
        print_doc(doc)

    # ── remove task ──────────────────────────────────────────────────────────
    elif args.rm:
        words = normalize_args(args.rm)
        tag_path, rest = extract_tags_and_text(words)
        try:
            n = int(rest[0]) if rest else int(words[-1])
        except (ValueError, IndexError):
            print("Error: -r needs a task number.", file=sys.stderr); sys.exit(1)
        node = navigate_to_tag(doc, tag_path) if tag_path else doc
        if node is None:
            print("Error: tag path not found.", file=sys.stderr); sys.exit(1)
        tasks = node.get("tasks", [])
        if n < 1 or n > len(tasks):
            print(f"Error: no task #{n} here.", file=sys.stderr); sys.exit(1)
        removed = tasks.pop(n - 1)
        save(doc, effective_pw)
        print(f"Removed: {removed['text']}")
        print_doc(doc)

    # ── remove tag ───────────────────────────────────────────────────────────
    elif args.rmtag:
        words = args.rmtag
        tag_path, rest = extract_tags_and_text(words)
        if tag_path:
            parent_path = tag_path[:-1]
            child_name  = tag_path[-1]
            parent = navigate_to_tag(doc, parent_path) if parent_path else doc
            if parent is None:
                print("Error: path not found.", file=sys.stderr); sys.exit(1)
            target = next((t for t in parent.get("tags", []) if t["name"] == child_name), None)
        elif rest:
            try:
                n = int(rest[0])
                target, parent = find_tag_by_number(doc, n)
            except ValueError:
                print("Error: expected a tag number or #name.", file=sys.stderr); sys.exit(1)
        else:
            print("Error: specify tag to remove.", file=sys.stderr); sys.exit(1)

        if target is None:
            print("Error: tag not found.", file=sys.stderr); sys.exit(1)
        tc = count_tasks_recursive(target)
        confirm = input(f"  Delete #{target['name']} and {tc} task(s) inside? [y/N] ").strip()
        if confirm.lower() == "y":
            parent["tags"].remove(target)
            save(doc, effective_pw)
            print(f"Removed tag: #{target['name']}")
            print_doc(doc)

    # ── toggle done ──────────────────────────────────────────────────────────
    elif args.done:
        words = normalize_args(args.done)
        tag_path, rest = extract_tags_and_text(words)
        try:
            n = int(rest[0]) if rest else int(words[-1])
        except (ValueError, IndexError):
            print("Error: -d needs a task number.", file=sys.stderr); sys.exit(1)
        node = navigate_to_tag(doc, tag_path) if tag_path else doc
        if node is None:
            print("Error: tag path not found.", file=sys.stderr); sys.exit(1)
        tasks = node.get("tasks", [])
        if n < 1 or n > len(tasks):
            print(f"Error: no task #{n} there.", file=sys.stderr); sys.exit(1)
        tasks[n - 1]["done"] = not tasks[n - 1]["done"]
        state = "done" if tasks[n - 1]["done"] else "undone"
        save(doc, effective_pw)
        print(f"Marked {state}: {tasks[n-1]['text']}")
        print_doc(doc)

    # ── edit ─────────────────────────────────────────────────────────────────
    elif args.edit:
        words = args.edit
        tag_path, rest = extract_tags_and_text(words)
        try:
            n = int(rest[0]); new_words = rest[1:]
        except (ValueError, IndexError):
            print("Error: -e [#tag] N new text", file=sys.stderr); sys.exit(1)
        node = navigate_to_tag(doc, tag_path) if tag_path else doc
        if node is None:
            print("Error: tag path not found.", file=sys.stderr); sys.exit(1)
        tasks = node.get("tasks", [])
        if n < 1 or n > len(tasks):
            print(f"Error: no task #{n}.", file=sys.stderr); sys.exit(1)
        p = parse_task_input(new_words)
        if p["text"]:     tasks[n-1]["text"]     = p["text"]
        if p["priority"]: tasks[n-1]["priority"] = p["priority"]
        if p["due"]:      tasks[n-1]["due"]       = p["due"]
        save(doc, effective_pw)
        print(f"Updated: {tasks[n-1]['text']}")
        print_doc(doc)

    # ── move ─────────────────────────────────────────────────────────────────
    elif args.move:
        words = args.move
        tag_path, rest = extract_tags_and_text(words)
        try:
            n = int(rest[0]); direction = rest[1].lower()
        except (ValueError, IndexError):
            print("Error: -m [#tag] N up|down", file=sys.stderr); sys.exit(1)
        node = navigate_to_tag(doc, tag_path) if tag_path else doc
        if node is None:
            print("Error: tag path not found.", file=sys.stderr); sys.exit(1)
        tasks = node.get("tasks", [])
        if n < 1 or n > len(tasks):
            print(f"Error: no task #{n}.", file=sys.stderr); sys.exit(1)
        idx = n - 1
        if direction == "up" and idx > 0:
            tasks[idx], tasks[idx-1] = tasks[idx-1], tasks[idx]
        elif direction == "down" and idx < len(tasks) - 1:
            tasks[idx], tasks[idx+1] = tasks[idx+1], tasks[idx]
        else:
            print("Already at edge.")
        save(doc, effective_pw)
        print_doc(doc)

    # ── search ────────────────────────────────────────────────────────────────
    elif args.search:
        keyword = " ".join(args.search).lower()
        def search_node(node, path=""):
            results = []
            for t in node.get("tasks", []):
                if keyword in t["text"].lower():
                    results.append((path, t))
            for tag in node.get("tags", []):
                p = f"{path}#{tag['name']} " if path else f"#{tag['name']} "
                results.extend(search_node(tag, p))
            return results
        matches = search_node(doc)
        if not matches:
            print(f"  {DIM}No matches for '{keyword}'{RST}")
        else:
            print(f"  {BOLD}{len(matches)} result(s):{RST}")
            for path, t in matches:
                pri = t.get("priority"); pc = PRIORITY_COLOR.get(pri, "")
                check = f"{DIM}[x]{RST}" if t["done"] else "[ ]"
                print(f"  {check} {DIM}{path}{RST}{pc}{t['text']}{RST}{due_label(t.get('due'))}")

    # ── clear ─────────────────────────────────────────────────────────────────
    elif args.clear:
        confirm = input("  Clear ALL tasks? This cannot be undone. [y/N] ")
        if confirm.lower() == "y":
            new_doc = empty_doc()
            save(new_doc, effective_pw)
            print("  Cleared.")

    # ── interactive ───────────────────────────────────────────────────────────
    elif args.interactive:
        interactive(doc, password=effective_pw)

    # ── positional: todo #work or todo #2 ────────────────────────────────────
    elif args.positional:
        arg = args.positional[0]
        if arg.startswith("#"):
            name = arg[1:].lower()
            try:
                n = int(name)
                tag, _ = find_tag_by_number(doc, n)
            except ValueError:
                tag = navigate_to_tag(doc, [name])
            if tag is None:
                print(f"  Tag '{arg}' not found.", file=sys.stderr); sys.exit(1)
            print(f"\n  {TAG_COLORS[0]}{BOLD}#{tag['name']}{RST}\n")
            print_doc(tag, show_all=True)
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr); sys.exit(1)

    # ── default: collapsed view ───────────────────────────────────────────────
    else:
        print_doc(doc, show_all=args.all)


if __name__ == "__main__":
    main()
