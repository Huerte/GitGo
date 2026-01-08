#!/bin/sh
# GitGo Uninstaller for Linux/Termux
# Cross-platform uninstallation script

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

print_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

print_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

print_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}

print_header() {
    echo ""
    echo "========================================"
    echo "   GitGo Uninstaller v1.0"
    echo "========================================"
    echo ""
}

# Detect if running in Termux
is_termux() {
    if [ -n "$PREFIX" ] && [ -d "/data/data/com.termux" ]; then
        return 0
    fi
    return 1
}

main() {
    print_header
    
    if is_termux; then
        PLATFORM="Termux"
        INSTALL_DIR="${PREFIX}/share/gitgo"
        BIN_DIR="${PREFIX}/bin"
    else
        PLATFORM="Linux"
        INSTALL_DIR="$HOME/.local/share/gitgo"
        BIN_DIR="$HOME/.local/bin"
    fi
    
    print_info "Platform detected: $PLATFORM"
    print_warning "This will remove GitGo from your system."
    
    printf "Are you sure you want to continue? (y/N): "
    read -r response
    
    case "$response" in
        [yY][eE][sS]|[yY]) 
            ;;
        *)
            print_info "Uninstallation cancelled."
            exit 0
            ;;
    esac
    
    echo ""
    
    WRAPPER_PATH="$BIN_DIR/gitgo"
    
    if [ -f "$WRAPPER_PATH" ]; then
        print_info "Removing wrapper script..."
        rm -f "$WRAPPER_PATH"
        print_success "Wrapper script removed: $WRAPPER_PATH"
    else
        print_warning "Wrapper script not found: $WRAPPER_PATH"
    fi
    
    if [ -d "$INSTALL_DIR" ]; then
        print_info "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
        print_success "Installation directory removed: $INSTALL_DIR"
    else
        print_warning "Installation directory not found: $INSTALL_DIR"
    fi
    
    if command -v gitgo >/dev/null 2>&1; then
        print_warning "GitGo command is still accessible from PATH."
        print_warning "This might be from a different installation."
        print_info "Location: $(which gitgo)"
    else
        print_success "GitGo command removed from system."
    fi
    
    echo ""
    echo "========================================"
    echo "   Uninstallation Complete!"
    echo "========================================"
    echo ""
    print_info "GitGo has been removed from your system."
    
    print_info "Note: If you manually added $BIN_DIR to your PATH,"
    print_info "you may want to remove it from your shell configuration file."
    echo ""
}

main
