#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_banner() {
    echo ""
    echo -e "${GREEN}╭────────────────────────────────────────────╮${NC}"
    echo -e "${GREEN}│                 GitGo CLI                  │${NC}"
    echo -e "${GREEN}│          ${CYAN}Your Fast Git Companion${GREEN}           │${NC}"
    echo -e "${GREEN}╰────────────────────────────────────────────╯${NC}"
    echo ""
}

show_banner

echo -e "${BLUE}Installing GitGo CLI...${NC}"

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: python3 is required but not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo -e "${RED}Error: Python 3.8+ is required, found $PYTHON_VERSION.${NC}"
    echo "Please upgrade Python and try again."
    exit 1
fi

INSTALL_DIR="$HOME/.gitgo"

# Termux doesn't use ~/.local/bin as a standard PATH location, so use its own bin dir instead.
if [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"com.termux"* ]]; then
    BIN_DIR="$PREFIX/bin"
else
    BIN_DIR="$HOME/.local/bin"
fi

if [ -d "$INSTALL_DIR/venv" ]; then
    echo "Removing previous installation..."
    rm -rf "$INSTALL_DIR/venv"
fi

echo "Creating isolated Python environment in $INSTALL_DIR/venv..."
if ! python3 -m venv "$INSTALL_DIR/venv"; then
    echo -e "${RED}Failed to create virtual environment.${NC}"
    echo "You may need to install the venv package for your system."
    echo "For example, on Ubuntu/Debian: sudo apt install python3-venv"
    exit 1
fi

echo "Installing pygitgo from PyPI..."
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pygitgo

mkdir -p "$BIN_DIR"

# Warn before overwriting anything at $BIN_DIR/gitgo that isn't ours
if [ -e "$BIN_DIR/gitgo" ] && [ ! -L "$BIN_DIR/gitgo" ]; then
    echo -e "${YELLOW}Warning: $BIN_DIR/gitgo already exists and isn't a GitGo-managed symlink. It will be overwritten.${NC}"
fi

ln -sf "$INSTALL_DIR/venv/bin/gitgo" "$BIN_DIR/gitgo"

# Verify the linked binary actually runs before declaring success
if ! "$BIN_DIR/gitgo" -v >/dev/null 2>&1; then
    echo -e "${RED}Installed, but $BIN_DIR/gitgo did not run successfully. Something went wrong.${NC}"
    exit 1
fi

echo -e "\n${GREEN}GitGo installed successfully!${NC}\n"

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Warning: $BIN_DIR is not in your PATH.${NC}"

    # Point at the profile file that actually matches the user's shell
    SHELL_NAME=$(basename "${SHELL:-bash}")
    case "$SHELL_NAME" in
        zsh)  PROFILE_FILE="~/.zshrc" ;;
        fish) PROFILE_FILE="~/.config/fish/config.fish" ;;
        *)    PROFILE_FILE="~/.bashrc" ;;
    esac

    echo "To use gitgo from anywhere, add the following to your shell profile ($PROFILE_FILE):"
    if [ "$SHELL_NAME" = "fish" ]; then
        echo -e "\n    set -gx PATH $BIN_DIR \$PATH\n"
    else
        echo -e "\n    export PATH=\"$BIN_DIR:\$PATH\"\n"
    fi
    echo "After adding it, restart your terminal or run: source $PROFILE_FILE"
else
    echo -e "You can now run ${BLUE}gitgo${NC} from anywhere."
    echo "Try running: gitgo -r"
fi