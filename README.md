# todo

Ultra-light personal CLI task manager. Nested tags, priorities, due dates, optional encryption.

[![Python](https://img.shields.io/badge/python-3.8%2B-000?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-000?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/v1.0.0-000?style=flat-square)](CHANGELOG.md)
[![Website](https://img.shields.io/badge/website-000?style=flat-square)](https://luuucciiffeerr.github.io/TODO/)

---

## Install

**Linux / macOS**
```bash
curl -fsSL https://raw.githubusercontent.com/luuucciiffeerr/TODO/main/install.sh | bash
```

**Windows (PowerShell)**
```powershell
irm https://raw.githubusercontent.com/luuucciiffeerr/TODO/main/install.ps1 | iex
```

**Manual**
```bash
cp todo.py ~/.local/bin/todo.py
echo 'exec python3 ~/.local/bin/todo.py "$@"' > ~/.local/bin/todo
chmod +x ~/.local/bin/todo
```

---

## Usage

```bash
todo -a buy milk                       # add a task
todo -a #work fix bug !1 @2026-06-15  # tagged + priority + due
todo                                   # view all tasks
todo -d 1                              # toggle done
todo -r 1                              # remove task
todo -e 2 new text                     # edit task
todo -m 2 up                           # reorder
todo -s keyword                        # search
todo -i                                # interactive TUI
todo --help                            # full reference
```

---

## Features

- **Nested tags** — `#work #backend` hierarchies
- **Priorities** — `!1` (high), `!2` (medium), `!3` (normal)
- **Due dates** — `@YYYY-MM-DD`, overdue highlighting
- **Encryption** — AES/Fernet via `todo --encrypt` (PBKDF2-HMAC-SHA256, 480k iterations)
- **Per-user data** — each OS user has their own isolated task file
- **Interactive TUI** — arrow-key navigation on Linux, macOS, and Windows
- **Atomic writes** — data saved via tmp + rename, safe on crash
- **Zero required dependencies** — works with Python 3.8+
- **Single file** — the entire app is `todo.py`

---

## Encryption

```bash
pip install cryptography
todo --encrypt
```

Password via `TODO_PASSWORD` environment variable.

No password recovery. Back up `.salt` alongside `tasks.json`.

---

## Data location

| OS | Path |
|---|---|
| Linux | `~/.local/share/todo/tasks.json` |
| macOS | `~/.local/share/todo/tasks.json` |
| Windows | `%APPDATA%\todo\tasks.json` |

---

## License

MIT — see [LICENSE](LICENSE).

[Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Website](https://luuucciiffeerr.github.io/TODO/)
