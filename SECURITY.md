# Security

## Data Storage

Your tasks are stored locally on your machine — no cloud sync, no remote servers, no telemetry.

| OS | Default location |
|---|---|
| Linux | `~/.local/share/todo/tasks.json` |
| macOS | `~/.local/share/todo/tasks.json` |
| Windows | `%APPDATA%\todo\tasks.json` |

On Linux and macOS the data directory is created with `chmod 700` (owner-only access) and the data file with `chmod 600`. This means other users on the same machine cannot read your tasks even in unencrypted mode.

## Optional Encryption

Enable end-to-end encryption of your task data with one command:

```
pip install cryptography
todo --encrypt
```

**What it does:**
- Encrypts `tasks.json` using AES-128-CBC (via [Fernet](https://cryptography.io/en/latest/fernet/))
- Derives the key from your password using **PBKDF2-HMAC-SHA256** with 480,000 iterations (NIST 2023 recommendation)
- A random 32-byte salt is stored separately in `.salt` (owner-read-only on Unix)
- Writes are **atomic**: data is written to a `.tmp` file and then renamed to prevent corruption on crash

**Important:**
- There is **no password recovery**. If you forget your password, your encrypted data cannot be recovered.
- The salt file (`.salt`) must not be deleted — it is needed to derive the key.
- Make backups of both `tasks.json` and `.salt` if you use encryption.

## Password Handling

- Passwords are never stored anywhere on disk.
- You can pass the password via the `TODO_PASSWORD` environment variable to avoid repeated prompts (e.g. in scripts). This is safer than using `--password` on the command line, which may appear in shell history and `ps` output.
- The `--password` CLI flag is provided for scripting convenience; be aware of the shell-history risk.

## Threat Model

todo is designed to protect your tasks from:
- Other users on the same OS account system (filesystem permissions)
- Accidental exposure when unencrypted files are copied or shared (encryption)

todo does **not** protect against:
- A compromised OS or root-level attacker
- Keyloggers capturing your password
- An attacker with physical access to your unlocked machine

## Reporting a Vulnerability

Open an issue on GitHub with the `security` label, or email the maintainer directly. Please do not publicly disclose security issues before they are fixed.
