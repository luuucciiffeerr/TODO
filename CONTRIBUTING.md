# Contributing

Thanks for wanting to improve todo. Here's how.

## Philosophy

- **One file**: the entire app is `todo.py`. Keep it that way.
- **Zero required dependencies**: the app must work with a standard Python 3.8 install.
- **Per-user isolation**: nothing should be written to shared or system-wide locations without explicit user consent.
- **Cross-platform**: every change should work on Linux, macOS, and Windows.

## Getting started

```bash
git clone https://github.com/luuucciiffeerr/todo.git
cd todo
python todo.py --help       # test the local copy
```

No build step, no virtual environment needed unless you're testing encryption:

```bash
pip install cryptography    # optional — only for encryption features
python todo.py --encrypt
```

## Running the tests

```bash
python -m pytest tests/ -v
```

If tests don't exist yet for a feature, add them in `tests/test_todo.py`.

## Submitting a pull request

1. Fork the repository
2. Create a branch: `git checkout -b fix/describe-your-change`
3. Make your change in `todo.py`
4. Test on at least one OS (Linux, macOS, or Windows)
5. Summarise the change in `CHANGELOG.md` under `[Unreleased]`
6. Open a pull request with a clear description

## Style

- Follow PEP 8
- Prefer clarity over cleverness
- Keep functions small and focused
- Add a docstring to any new public function

## What we won't accept

- Cloud sync or remote storage of any kind
- Required new dependencies
- UI that requires a terminal emulator beyond basic ANSI
- Behaviour that differs between platforms without a clear reason

## Security issues

See [SECURITY.md](SECURITY.md).
