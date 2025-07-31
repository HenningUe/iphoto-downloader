#!/bin/bash
# Linux build script for iPhoto Downloader Tool
# Builds a Linux executable using PyInstaller

set -euo pipefail

# Default values
CLEAN=false
TEST=false
OUTPUT_DIR="dist"
CREDENTIALS_ONLY=false
MAIN_ONLY=false

# Check if required files exist
echo "📋 Checking required files..."
REQUIRED_FILES=("USER-GUIDE.md" ".env.example" "iphoto_downloader.spec" "iphoto_downloader_credentials.spec")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done
echo "✅ All required files present"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --credentials-only)
            CREDENTIALS_ONLY=true
            shift
            ;;
        --main-only)
            MAIN_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--test] [--output-dir DIR] [--credentials-only] [--main-only]"
            echo "  --clean           Clean previous builds"
            echo "  --test            Test the built executable(s)"
            echo "  --output-dir      Specify output directory (default: dist)"
            echo "  --credentials-only Build only credentials manager"
            echo "  --main-only       Build only main executable"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Display version information
VERSION_FILE="VERSION"
VERSION="dev"
if [ -f "$VERSION_FILE" ]; then
    VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r')
fi

echo "🚀 Building iPhoto Downloader Tool v$VERSION for Linux"
echo "======================================================="

# Check if running in correct directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Must run from repository root directory"
    exit 1
fi

# Check if uv is available, install if not
UV_COMMAND=""

# First check in local virtual environment (preferred)
# Use Windows path structure for .venv
if [ -f ".venv/Scripts/uv" ] || [ -f ".venv/Scripts/uv.exe" ]; then
    if [ -f ".venv/Scripts/uv.exe" ]; then
        UV_COMMAND=".venv/Scripts/uv.exe"
    else
        UV_COMMAND=".venv/Scripts/uv"
    fi
    echo "✅ Found uv in virtual environment: $UV_COMMAND"
# Also check Linux/macOS path structure for cross-compatibility
elif [ -f ".venv/bin/uv" ]; then
    UV_COMMAND=".venv/bin/uv"
    echo "✅ Found uv in virtual environment: $UV_COMMAND"
# Then check global uv
elif command -v uv &> /dev/null; then
    UV_COMMAND="uv"
    echo "✅ Found uv globally: $(which uv)"
else
    echo "⚠️  uv not found. Attempting to install..."
    
    # Check if pip is available
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo "❌ Neither uv nor pip is installed. Please install Python with pip first."
        exit 1
    fi
    
    # Determine which pip to use
    PIP_COMMAND="pip"
    if command -v pip3 &> /dev/null; then
        PIP_COMMAND="pip3"
    elif command -v pip &> /dev/null; then
        PIP_COMMAND="pip"
    fi
    
    # Try to install uv using pip
    echo "📦 Installing uv using $PIP_COMMAND..."
    if ! "$PIP_COMMAND" install --user uv; then
        echo "❌ Failed to install uv automatically. Please install manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   or: pip install uv"
        exit 1
    fi
    
    echo "✅ uv installed successfully"
    
    # Refresh PATH for current session and check common installation paths
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    # Wait a moment for installation to complete
    sleep 1
    
    # Check again with refreshed PATH, but prefer .venv first
    if [ -f ".venv/Scripts/uv" ] || [ -f ".venv/Scripts/uv.exe" ]; then
        if [ -f ".venv/Scripts/uv.exe" ]; then
            UV_COMMAND=".venv/Scripts/uv.exe"
        else
            UV_COMMAND=".venv/Scripts/uv"
        fi
        echo "✅ uv now available in virtual environment: $UV_COMMAND"
    elif [ -f ".venv/bin/uv" ]; then
        UV_COMMAND=".venv/bin/uv"
        echo "✅ uv now available in virtual environment: $UV_COMMAND"
    elif command -v uv &> /dev/null; then
        UV_COMMAND="uv"
        echo "✅ uv now available globally"
    else
        echo "⚠️  uv was installed but not found in PATH. Trying to locate it..."
        
        # Try common installation paths with more comprehensive search
        # Prioritize .venv first (Windows and Linux paths), then other locations
        POSSIBLE_PATHS=(
            ".venv/Scripts/uv.exe"
            ".venv/Scripts/uv"
            ".venv/bin/uv"
            "$HOME/.local/bin/uv"
            "$HOME/.cargo/bin/uv"
            "$HOME/bin/uv"
            "$HOME/.local/share/uv/bin/uv"
            "/usr/local/bin/uv"
            "/opt/local/bin/uv"
        )
        
        # Also search in Python site-packages directories
        if command -v python3 &> /dev/null; then
            PYTHON_USER_BASE=$(python3 -m site --user-base 2>/dev/null || echo "")
            if [ -n "$PYTHON_USER_BASE" ]; then
                POSSIBLE_PATHS+=("$PYTHON_USER_BASE/bin/uv")
            fi
        fi
        
        # Search for uv in common pip installation directories
        for pip_dir in "$HOME/.local/bin" "$HOME/Library/Python/"*/bin "$HOME/.local/lib/python"*/site-packages/bin; do
            if [ -d "$pip_dir" ]; then
                POSSIBLE_PATHS+=("$pip_dir/uv")
            fi
        done
        
        # Debug: Show what paths we're checking
        echo "   Checking paths:"
        for path in "${POSSIBLE_PATHS[@]}"; do
            echo "     - $path"
            if [ -f "$path" ] && [ -x "$path" ]; then
                UV_COMMAND="$path"
                echo "✅ Found uv at: $UV_COMMAND"
                break
            fi
        done
        
        # If still not found, try a more aggressive search
        if [ -z "$UV_COMMAND" ]; then
            echo "   Performing comprehensive search..."
            # Search in home directory and common locations
            FOUND_UV=$(find "$HOME" /usr/local /opt -name "uv" -type f -executable 2>/dev/null | head -1)
            if [ -n "$FOUND_UV" ]; then
                UV_COMMAND="$FOUND_UV"
                echo "✅ Found uv at: $UV_COMMAND"
            fi
        fi
        
        if [ -z "$UV_COMMAND" ]; then
            echo "❌ uv installation failed or not found in expected locations."
            echo "   Searched paths:"
            for path in "${POSSIBLE_PATHS[@]}"; do
                echo "     $path"
            done
            echo ""
            echo "   Please try one of these alternatives:"
            echo "   1. Manual installation: curl -LsSf https://astral.sh/uv/install.sh | sh"
            echo "   2. Install via package manager: sudo apt install uv (if available)"
            echo "   3. Add uv to your PATH manually"
            echo "   4. Use pipx: pipx install uv"
            echo "   5. Create virtual environment with uv: python3 -m venv .venv && .venv/Scripts/pip install uv (Windows) or .venv/bin/pip install uv (Linux/macOS)"
            exit 1
        fi
    fi
fi

echo "🔧 Using uv: $UV_COMMAND"

# Clean previous builds if requested
if [ "$CLEAN" = true ]; then
    echo "🧹 Cleaning previous builds..."
    rm -rf build/ "$OUTPUT_DIR"/ __pycache__/
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    echo "✅ Cleaned build directories"
fi

# Install dependencies
echo "📦 Installing dependencies..."
if ! "$UV_COMMAND" sync --dev; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

# Verify required files exist
echo "🔍 Verifying required files..."
REQUIRED_FILES=("USER-GUIDE.md" ".env.example" "iphoto_downloader.spec" "iphoto_downloader_credentials.spec")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done
echo "✅ All required files present"

# Check for development packages that might be needed
echo "🔍 Checking system dependencies..."
MISSING_DEPS=()

# Check for development headers (needed for some Python packages)
if ! dpkg -l | grep -q python3-dev 2>/dev/null && ! rpm -q python3-devel 2>/dev/null; then
    MISSING_DEPS+=("python3-dev or python3-devel")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠️  Warning: Some system dependencies might be missing:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "   - $dep"
    done
    echo "   Install with: sudo apt install python3-dev (Ubuntu/Debian)"
    echo "               or: sudo yum install python3-devel (CentOS/RHEL)"
fi

# Build executable with PyInstaller
echo "🔨 Building Linux executable(s)..."

# Build main executable (unless credentials-only is specified)
if [ "$CREDENTIALS_ONLY" = false ]; then
    echo "🔧 Building main iPhoto Downloader executable..."
    if ! "$UV_COMMAND" run python -m PyInstaller iphoto_downloader.spec --distpath "$OUTPUT_DIR" --workpath build; then
        echo "❌ Main executable build failed"
        exit 1
    fi
    echo "✅ Main executable build completed successfully"
fi

# Build credentials manager executable (unless main-only is specified)
if [ "$MAIN_ONLY" = false ]; then
    echo "🔧 Building credentials manager executable..."
    if ! "$UV_COMMAND" run python -m PyInstaller iphoto_downloader_credentials.spec --distpath "$OUTPUT_DIR" --workpath build; then
        echo "❌ Credentials manager build failed"
        exit 1
    fi
    echo "✅ Credentials manager build completed successfully"
fi

# Verify build output
MAIN_EXE_PATH="$OUTPUT_DIR/iphoto_downloader"
CRED_EXE_PATH="$OUTPUT_DIR/iphoto_downloader_credentials"

echo "📊 Build Information:"

# Check main executable
if [ "$CREDENTIALS_ONLY" = false ] && [ -f "$MAIN_EXE_PATH" ]; then
    chmod +x "$MAIN_EXE_PATH"
    MAIN_EXE_SIZE=$(du -m "$MAIN_EXE_PATH" | cut -f1)
    echo "   Main Executable: $MAIN_EXE_PATH"
    echo "   Main Size: ${MAIN_EXE_SIZE} MB"
    echo "   Main Permissions: $(ls -la "$MAIN_EXE_PATH" | cut -d' ' -f1)"
elif [ "$CREDENTIALS_ONLY" = false ]; then
    echo "❌ Main executable not found at expected location: $MAIN_EXE_PATH"
    exit 1
fi

# Check credentials manager executable
if [ "$MAIN_ONLY" = false ] && [ -f "$CRED_EXE_PATH" ]; then
    chmod +x "$CRED_EXE_PATH"
    CRED_EXE_SIZE=$(du -m "$CRED_EXE_PATH" | cut -f1)
    echo "   Credentials Manager: $CRED_EXE_PATH"
    echo "   Credentials Size: ${CRED_EXE_SIZE} MB"
    echo "   Credentials Permissions: $(ls -la "$CRED_EXE_PATH" | cut -d' ' -f1)"
elif [ "$MAIN_ONLY" = false ]; then
    echo "❌ Credentials manager executable not found at expected location: $CRED_EXE_PATH"
    exit 1
fi

# Test executable if requested
if [ "$TEST" = true ]; then
    echo "🧪 Testing executable..."
    
    # Determine which executable to test
    if [ "$CREDENTIALS_ONLY" = true ]; then
        EXE_PATH="$CRED_EXE_PATH"
    else
        EXE_PATH="$MAIN_EXE_PATH"
    fi
    
    # Test basic startup (should exit quickly in Delivered mode without settings)
    if "$EXE_PATH" --help >/dev/null 2>&1; then
        echo "✅ Executable starts successfully"
    else
        EXIT_CODE=$?
        echo "⚠️  Executable exit code: $EXIT_CODE"
    fi
    
    # Check if executable has proper dependencies
    echo "🔍 Checking executable dependencies..."
    if command -v ldd &> /dev/null; then
        echo "   Shared library dependencies:"
        ldd "$EXE_PATH" | head -10
        if ldd "$EXE_PATH" | grep -q "not found"; then
            echo "⚠️  Some shared libraries not found. This may cause issues on other systems."
        else
            echo "✅ All dependencies found"
        fi
    else
        echo "   ldd not available, skipping dependency check"
    fi
    
    # Check for static linking level
    if command -v file &> /dev/null; then
        FILE_INFO=$(file "$EXE_PATH")
        echo "   File type: $FILE_INFO"
        if echo "$FILE_INFO" | grep -q "statically linked"; then
            echo "✅ Executable is statically linked"
        else
            echo "ℹ️  Executable is dynamically linked"
        fi
    fi
fi

echo ""
echo "🎉 Linux build completed successfully!"
echo "📁 Output location: $OUTPUT_DIR"
echo "🚀 Ready for distribution"

# Display next steps
echo ""
echo "📋 Next Steps:"
echo "1. Test the executable on various Linux distributions"
echo "2. Verify delivery artifacts creation in Delivered mode"
echo "3. Test 2FA functionality and Pushover notifications"
echo "4. Package for distribution (AppImage, deb, rpm, etc.)"
echo ""
echo "💡 For AppImage creation:"
echo "   Use linuxdeploy or appimagetool with the built executable"
echo "💡 For deb package:"
echo "   Use fpm: fpm -s dir -t deb -n iphoto-downloader ..."
echo "💡 For rpm package:"
echo "   Use fpm: fpm -s dir -t rpm -n iphoto-downloader ..."
