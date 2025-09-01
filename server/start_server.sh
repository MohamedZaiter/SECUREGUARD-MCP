#!/bin/bash
# SecureGuard MCP Server Startup Script
set -euo pipefail

echo -e "\n🛡️  \033[1mSecureGuard MCP Server\033[0m"
echo "======================="

# Check if running from the correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to display error messages
error_exit() {
    echo -e "❌ \033[1;31m$1\033[0m" >&2
    exit 1
}

# Check Python installation
if ! command -v python3 &>/dev/null; then
    error_exit "Python 3.7+ is required but not installed. Please install it and try again."
fi

# Verify Python version
PYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
if [[ "$(printf '%s\n' "3.7" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.7" ]]; then
    error_exit "Python 3.7 or higher is required. Found Python $PYTHON_VERSION"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f "../.env.template" ]; then
        cp "../.env.template" ".env"
        echo "ℹ️  Created .env file from template. Please update with your configuration."
    else
        echo "⚠️  No .env.template found. Please create a .env file manually."
    fi
fi

# Install/update dependencies
echo -e "\n📦 Setting up Python environment..."
python3 -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    touch .deps_installed
    echo "✅ Dependencies installed/updated"
else
    error_exit "requirements.txt not found"
fi

# Check if mcp_server.py exists
if [ ! -f "mcp_server.py" ]; then
    error_exit "mcp_server.py not found in current directory"
fi

echo "🚀 Starting MCP Server on port 9002..."
$PYTHON_CMD mcp_server.py