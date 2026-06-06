#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  todo — uninstall script for Linux & macOS
#  Usage:  bash uninstall.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

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

echo -e "${BOLD}"
echo "  ████████╗ ██████╗ ██████╗  ██████╗ "
echo "     ██╔══╝██╔═══██╗██╔══██╗██╔═══██╗"
echo "     ██║   ██║   ██║██║  ██║██║   ██║"
echo "     ██║   ██║   ██║██║  ██║██║   ██║"
echo "     ██║   ╚██████╔╝██████╔╝╚██████╔╝"
echo "     ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ "
echo -e "${RST}${DIM}  uninstall${RST}"
echo ""

# ── Locate installation ──────────────────────────────────────────────────────
info "Looking for todo..."
TODO_PATH=""
for p in /usr/local/bin/todo ~/.local/bin/todo; do
    if [ -f "$p" ]; then
        TODO_PATH="$p"
        break
    fi
done

if [ -z "$TODO_PATH" ]; then
    # Check custom PATH
    if command -v todo &>/dev/null; then
        TODO_PATH="$(command -v todo)"
    else
        error "todo not found on your system."
    fi
fi

INSTALL_DIR="$(dirname "$TODO_PATH")"
echo ""
warn "This will remove todo from: $INSTALL_DIR"
echo -e "  ${DIM}Data directory will also be removed.${RST}"
echo ""
read -rp "  Continue? [y/N] " CONFIRM
if [ "${CONFIRM:-n}" != "y" ]; then
    echo "  Aborted."
    exit 0
fi

# ── Remove files ─────────────────────────────────────────────────────────────
info "Removing todo files..."
rm -f "$INSTALL_DIR/todo" "$INSTALL_DIR/todo.py"
success "Removed todo from $INSTALL_DIR"

# ── Remove data directory ─────────────────────────────────────────────────────
DATA_DIR="${HOME}/.local/share/todo"
if [ -d "$DATA_DIR" ]; then
    echo ""
    warn "Remove your task data at $DATA_DIR?"
    read -rp "  Remove all data? [y/N] " DATA_CONFIRM
    if [ "${DATA_CONFIRM:-n}" == "y" ]; then
        rm -rf "$DATA_DIR"
        success "Data removed."
    else
        warn "Data kept at $DATA_DIR"
    fi
fi

echo ""
echo -e "${GREEN}Done.${RST}"
