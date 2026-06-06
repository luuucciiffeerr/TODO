<div align="center">

```
████████╗ ██████╗ ██████╗  ██████╗
   ██╔══╝██╔═══██╗██╔══██╗██╔═══██╗
   ██║   ██║   ██║██║  ██║██║   ██║
   ██║   ██║   ██║██║  ██║██║   ██║
   ██║   ╚██████╔╝██████╔╝╚██████╔╝
   ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝
```

**ultra-light. local. yours.**

[![Python](https://img.shields.io/badge/python-3.8%2B-black?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-black?style=flat-square)](.)
[![License](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-black?style=flat-square)](CHANGELOG.md)
[![No Cloud](https://img.shields.io/badge/cloud-none-black?style=flat-square)](SECURITY.md)
[![Site](https://img.shields.io/badge/website-githubpages-black?style=flat-square)](https://luuucciiffeerr.github.io/TODO/)

</div>

---

**todo** is a personal CLI task manager that lives entirely in your terminal.  
No accounts. No cloud. No background processes. Just a single Python file and your data.

```
$ todo -a #work fix the CI pipeline !1 @2026-06-10
Added to [#work]: fix the CI pipeline

$ todo
  > 1. #work (0/3)  >
  > 1. [ ]   grab groceries
  > 2. [x]   call the bank
```

---

## Features

- **Nested tags** — organize tasks with `#tag #subtag` chains
- **Priorities** — `!1` (urgent) · `!2` (medium) · `!3` (normal)
- **Due dates** — `@YYYY-MM-DD`, highlighted when overdue or close
- **Encryption** — optional AES/Fernet with PBKDF2 key derivation
- **Per-user data** — each OS user has their own isolated task list
- **Interactive TUI** — arrow-key navigation on all platforms
- **Zero dependencies** — works out of the box; encryption is opt-in
- **Single file** — the entire app is `todo.py`

---

## Install

### Linux & macOS

**One-line install:**

```bash
curl -fsSL https://raw.githubusercontent.com/luuucciiffeerr/TODO/main/install.sh | bash
```

**Or clone and run:**

```bash
git clone https://github.com/luuucciiffeerr/TODO.git
cd todo
bash install.sh
```

The installer will:
1. Check Python 3.8+
2. Optionally install the `cryptography` package
3. Ask whether to install globally (all users) or just for you
4. Offer to add the install directory to your `PATH` automatically

### Windows

**One-line install (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/luuucciiffeerr/TODO/main/install.ps1 | iex
```

**Or clone and run:**

```powershell
git clone https://github.com/luuucciiffeerr/TODO.git
cd todo
.\install.ps1
```

### Manual install (any OS)

```bash
# Copy todo.py somewhere on your PATH
cp todo.py ~/.local/bin/todo.py

# Create a launcher
echo '#!/bin/sh' > ~/.local/bin/todo
echo 'exec python3 ~/.local/bin/todo.py "$@"' >> ~/.local/bin/todo
chmod +x ~/.local/bin/todo
```

---

## Quick start

```bash
todo -a buy milk                       # add a task
todo -a #work fix bug !1 @2026-06-15  # tagged + priority + due date
todo                                   # view your list
todo -d 1                              # mark task #1 done
todo -r 1                              # remove task #1
todo --all                             # expand all tags
todo -i                                # interactive TUI
todo --help                            # full help
```

---

## Full command reference

```
USAGE
  todo                          show tasks (tags collapsed)
  todo --all                    expand everything
  todo #work                    open tag by name
  todo #2                       open tag by number

ADDING
  todo -a fix the bug           add task to root
  todo -a #work fix bug         add to tag 'work' (creates if missing)
  todo -a #work #backend bug    nested: work > backend
  todo -a !1 urgent thing       priority: !1=high  !2=med  !3=normal
  todo -a call dentist @2025-05-30   due date
  todo -a #work !1 @2025-05-30 deploy   all combined

MODIFYING
  todo -d 3                     toggle done on task #3
  todo -d #work 2               toggle done inside tag
  todo -e 2 new task text       edit task #2
  todo -m 2 up|down             reorder tasks

REMOVING
  todo -r 3                     remove task #3
  todo -r #work 2               remove inside tag
  todo --rmtag #work            remove tag + everything inside
  todo --rmtag 2                remove tag by number

SEARCH & MISC
  todo -s keyword               search all tasks (across all tags)
  todo --clear                  wipe everything (confirms)
  todo --version                print version

ENCRYPTION
  todo --encrypt                encrypt data with a password
  todo --decrypt                remove encryption
```

---

## Syntax

| Token | Meaning | Example |
|---|---|---|
| `!1` `!2` `!3` | Priority: high / medium / normal | `todo -a !1 urgent fix` |
| `@YYYY-MM-DD` | Due date | `todo -a call bank @2026-06-20` |
| `#tagname` | Tag (chain for nesting) | `todo -a #work #backend review PR` |

---

## Interactive TUI

Run `todo -i` for a full-screen interactive interface.

```
  > 1. #work  (2/5)  >
    > 1. [ ]   fix CI pipeline
    > 2. [x] ~ review PRs
  > 2. #personal  (1/3)  >
  > 1. [ ] ! urgent task  [today]

  ↑↓ move   → expand   ← collapse   Space done   d delete   a add   e edit   q quit
```

| Key | Action |
|---|---|
| `↑` `↓` | Navigate |
| `→` | Expand tag |
| `←` | Collapse tag |
| `Space` | Toggle done |
| `d` | Delete task or tag |
| `a` | Add task (context-aware) |
| `t` | New tag |
| `e` | Edit task / rename tag |
| `q` | Quit |

---

## Encryption

Your tasks can be encrypted at rest with one command:

```bash
pip install cryptography
todo --encrypt
```

**How it works:**
- AES-128-CBC encryption via Python's [Fernet](https://cryptography.io/en/latest/fernet/) standard
- Key derived from your password with **PBKDF2-HMAC-SHA256** (480,000 iterations — NIST 2023)
- Random 32-byte salt stored separately (`~/.local/share/todo/.salt`)
- Atomic writes (tmp → rename) prevent data loss on crash

**Password via environment variable** (safer for scripts — avoids shell history):

```bash
export TODO_PASSWORD="your-password"
todo -a new task
```

> ⚠️ There is no password recovery. Back up your `.salt` file alongside `tasks.json`.

---

## Data location

| OS | Path |
|---|---|
| Linux | `~/.local/share/todo/tasks.json` |
| macOS | `~/.local/share/todo/tasks.json` |
| Windows | `%APPDATA%\todo\tasks.json` |

The data directory is created with restricted permissions (`chmod 700` on Unix) so other users on the same system cannot read your tasks.

Each OS user has their own isolated data file.

---

## Uninstall

```bash
bash uninstall.sh
```

Or manually:

```bash
rm ~/.local/bin/todo ~/.local/bin/todo.py
rm -rf ~/.local/share/todo        # also removes your tasks data
```

---

## Requirements

- Python 3.8+
- `cryptography` *(optional, for encryption only)*

No other dependencies.

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-thing`
3. Make your changes in `todo.py`
4. Test on Linux, macOS, and Windows if possible
5. Open a pull request

Please keep the zero-dependency philosophy — the app should work with a standard Python installation.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**made to be used, not configured**

</div>
