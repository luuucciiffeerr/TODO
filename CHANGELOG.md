# Changelog

All notable changes to `todo` are documented here.

## [1.0.0] — 2026-06-06

### Added
- **Encryption** — optional AES/Fernet encryption via `todo --encrypt` / `todo --decrypt`
  - PBKDF2-HMAC-SHA256 key derivation (480,000 iterations)
  - Password can be supplied via `TODO_PASSWORD` env var
- **Cross-platform data directory** — per-user, OS-appropriate storage
  - Linux/macOS: `~/.local/share/todo/` (respects `$XDG_DATA_HOME`)
  - Windows: `%APPDATA%\todo\`
- **Per-user isolation** — each OS user has their own task list and salt
- **Filesystem security** — data dir `chmod 700`, file `chmod 600` on Unix
- **Atomic writes** — tasks saved via tmp + rename to prevent data loss on crash
- **Cross-platform interactive TUI** — arrow-key navigation on Linux/macOS (via `tty`/`termios`) and Windows (via `msvcrt`)
- **`--version` flag**
- **`TODO_PASSWORD` environment variable** support
- **`created` date field** on tasks
- **Install scripts** for Linux/macOS (`install.sh`) and Windows (`install.ps1`)
  - Interactive PATH setup
  - Per-user or global installation choice
  - Optional `cryptography` install

### Changed
- Data file renamed from `todo_data.json` to `tasks.json` (auto-migrated)
- Python version guard: exits with a clear message if Python < 3.8

### Fixed
- Interactive TUI was Windows-only; now works on Linux and macOS too

---

## [0.x] — Pre-release

Original single-file script with JSON task storage, nested tags, priorities, due dates, and Windows interactive TUI.
