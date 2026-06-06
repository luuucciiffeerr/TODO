#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  todo — install script for Linux & macOS
#  Usage:  bash install.sh
#  Or one-liner from GitHub:
#    curl -fsSL https://raw.githubusercontent.com/luuucciiffeerr/todo/main/install.sh | bash
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

VERSION="1.0.0"
REPO_URL="https://raw.githubusercontent.com/luuucciiffeerr/todo/main"
SCRIPT_NAME="todo.py"
WRAPPER_NAME="todo"

# ── Colours ──────────────────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RST='\033[0m'

info()    { echo -e "${CYAN}▶${RST} $*"; }
success() { echo -e "${GREEN}✓${RST} $*"; }
warn()    { echo -e "${YELLOW}⚠${RST} $*"; }
error()   { echo -e "${RED}✗${RST} $*"; exit 1; }
blank()   { echo; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo "  ████████╗ ██████╗ ██████╗  ██████╗ "
echo "     ██╔══╝██╔═══██╗██╔══██╗██╔═══██╗"
echo "     ██║   ██║   ██║██║  ██║██║   ██║"
echo "     ██║   ██║   ██║██║  ██║██║   ██║"
echo "     ██║   ╚██████╔╝██████╔╝╚██████╔╝"
echo "     ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ "
echo -e "${RST}${DIM}  ultra-light CLI task manager — v${VERSION}${RST}"
blank

# ── Python check ─────────────────────────────────────────────────────────────
info "Checking Python..."
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c 'import sys; print(sys.version_info >= (3, 8))' 2>/dev/null || echo "False")
        if [ "$VER" = "True" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    error "Python 3.8+ is required but not found.\nInstall it from https://python.org"
fi
PY_VER=$($PYTHON --version 2>&1)
success "Found $PY_VER"

# ── Optional: cryptography ────────────────────────────────────────────────────
blank
info "Checking optional encryption support..."
if $PYTHON -c "import cryptography" 2>/dev/null; then
    success "cryptography is installed — encryption available"
else
    warn "cryptography not installed (optional, enables 'todo --encrypt')"
    echo -e "  ${DIM}Install later with: pip install cryptography${RST}"
    blank
    read -rp "  Install now? [Y/n] " CRYPTO_ANSWER
    CRYPTO_ANSWER="${CRYPTO_ANSWER:-y}"
    if [[ "${CRYPTO_ANSWER,,}" == "y" ]]; then
        $PYTHON -m pip install cryptography --quiet && success "cryptography installed" || warn "Could not install — run manually later"
    fi
fi

# ── Locate or download todo.py ────────────────────────────────────────────────
blank
info "Locating todo.py..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "$PWD")"
if [ -f "$SCRIPT_DIR/todo.py" ]; then
    TODO_PY="$SCRIPT_DIR/todo.py"
    success "Found: $TODO_PY"
else
    info "Downloading from GitHub..."
    TMP=$(mktemp)
    if command -v curl &>/dev/null; then
        curl -fsSL "$REPO_URL/$SCRIPT_NAME" -o "$TMP" || error "Download failed"
    elif command -v wget &>/dev/null; then
        wget -q "$REPO_URL/$SCRIPT_NAME" -O "$TMP" || error "Download failed"
    else
        error "Neither curl nor wget found. Download todo.py manually."
    fi
    TODO_PY="$TMP"
    success "Downloaded todo.py"
fi

# ── Installation scope ────────────────────────────────────────────────────────
blank
echo -e "${BOLD}Installation type:${RST}"
echo "  1) ${BOLD}Global${RST}   — all users  (requires sudo, installs to /usr/local/bin)"
echo "  2) ${BOLD}User${RST}     — this user only  (installs to ~/.local/bin)"
echo "  3) ${BOLD}Custom${RST}   — specify your own directory"
blank
read -rp "  Choice [1/2/3, default=2]: " SCOPE
SCOPE="${SCOPE:-2}"

case "$SCOPE" in
    1)
        INSTALL_DIR="/usr/local/bin"
        USE_SUDO=true
        SCOPE_LABEL="global (all users)"
        ;;
    3)
        read -rp "  Install directory: " CUSTOM_DIR
        INSTALL_DIR="${CUSTOM_DIR/#\~/$HOME}"
        USE_SUDO=false
        SCOPE_LABEL="custom ($INSTALL_DIR)"
        ;;
    *)
        INSTALL_DIR="$HOME/.local/bin"
        USE_SUDO=false
        SCOPE_LABEL="user ($HOME/.local/bin)"
        ;;
esac

# ── Per-user data store clarification ─────────────────────────────────────────
blank
info "Data storage: each OS user has their own task list"
echo -e "  ${DIM}Linux/macOS: ~/.local/share/todo/tasks.json${RST}"
echo -e "  ${DIM}Windows:     %%APPDATA%%\\todo\\tasks.json${RST}"

# ── Install ───────────────────────────────────────────────────────────────────
blank
info "Installing to $INSTALL_DIR..."

if [ "$USE_SUDO" = true ]; then
    sudo mkdir -p "$INSTALL_DIR"
    sudo cp "$TODO_PY" "$INSTALL_DIR/todo.py"
    sudo chmod 755 "$INSTALL_DIR/todo.py"

    # Wrapper script
    sudo tee "$INSTALL_DIR/$WRAPPER_NAME" > /dev/null <<EOF
#!/usr/bin/env bash
exec $PYTHON "$INSTALL_DIR/todo.py" "\$@"
EOF
    sudo chmod 755 "$INSTALL_DIR/$WRAPPER_NAME"
else
    mkdir -p "$INSTALL_DIR"
    cp "$TODO_PY" "$INSTALL_DIR/todo.py"
    chmod 755 "$INSTALL_DIR/todo.py"

    cat > "$INSTALL_DIR/$WRAPPER_NAME" <<EOF
#!/usr/bin/env bash
exec $PYTHON "$INSTALL_DIR/todo.py" "\$@"
EOF
    chmod 755 "$INSTALL_DIR/$WRAPPER_NAME"
fi

success "Installed: $INSTALL_DIR/$WRAPPER_NAME"

# ── PATH setup ────────────────────────────────────────────────────────────────
blank
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    warn "$INSTALL_DIR is not in your PATH"
    blank
    echo -e "${BOLD}Add to PATH automatically?${RST}"
    echo "  This will append to your shell profile so 'todo' works globally."
    blank
    read -rp "  Add to PATH? [Y/n]: " PATH_ANSWER
    PATH_ANSWER="${PATH_ANSWER:-y}"

    if [[ "${PATH_ANSWER,,}" == "y" ]]; then
        SHELL_NAME=$(basename "$SHELL")
        case "$SHELL_NAME" in
            zsh)  PROFILE="$HOME/.zshrc" ;;
            fish) PROFILE="$HOME/.config/fish/config.fish" ;;
            *)    PROFILE="$HOME/.bashrc" ;;
        esac

        EXPORT_LINE="export PATH=\"$INSTALL_DIR:\$PATH\""
        if [ "$SHELL_NAME" = "fish" ]; then
            EXPORT_LINE="set -gx PATH \"$INSTALL_DIR\" \$PATH"
        fi

        echo "" >> "$PROFILE"
        echo "# todo — added by install.sh" >> "$PROFILE"
        echo "$EXPORT_LINE" >> "$PROFILE"

        success "Added to $PROFILE"
        export PATH="$INSTALL_DIR:$PATH"
        info "PATH updated for this session"
    fi
else
    success "$INSTALL_DIR already in PATH"
fi

# ── Verify ────────────────────────────────────────────────────────────────────
blank
info "Verifying installation..."
if command -v todo &>/dev/null; then
    todo --version
    success "todo is ready!"
else
    warn "Installed but 'todo' not found in current PATH."
    echo -e "  ${DIM}Run: source ~/.bashrc  (or open a new terminal)${RST}"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
blank
echo -e "${BOLD}${GREEN}All done! Get started:${RST}"
echo -e "  ${CYAN}todo -a my first task${RST}"
echo -e "  ${CYAN}todo --help${RST}"
blank
echo -e "${DIM}Data lives at: ~/.local/share/todo/tasks.json${RST}"
echo -e "${DIM}Docs:          https://github.com/luuucciiffeerr/todo${RST}"
blank
