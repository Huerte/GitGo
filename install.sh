#!/usr/bin/env bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing GitGo CLI...${NC}"

# Check for python3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: python3 is required but not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

INSTALL_DIR="$HOME/.gitgo"
BIN_DIR="$HOME/.local/bin"

# Remove old installation if exists
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

# Create bin directory if it doesn't exist
mkdir -p "$BIN_DIR"

# Link the executable
ln -sf "$INSTALL_DIR/venv/bin/gitgo" "$BIN_DIR/gitgo"

echo -e "\n${GREEN}✅ GitGo installed successfully!${NC}\n"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "⚠️  ${RED}Warning: $BIN_DIR is not in your PATH.${NC}"
    echo "To use gitgo from anywhere, add the following to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo -e "\n    export PATH=\"\$HOME/.local/bin:\$PATH\"\n"
    echo "After adding it, restart your terminal or run: source ~/.bashrc"
else
    echo -e "You can now run ${BLUE}gitgo${NC} from anywhere."
    echo "Try running: gitgo -r"
fi
