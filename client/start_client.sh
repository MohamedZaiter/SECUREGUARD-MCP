#!/bin/bash
# SecureGuard Web Client Startup Script
set -euo pipefail

echo -e "\n🌐 \033[1mSecureGuard Web Client\033[0m"
echo "=========================="

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

# Check if app.py exists
if [ ! -f "app.py" ]; then
    error_exit "app.py not found in current directory"
fi

# Check if templates directory exists
if [ ! -d "templates" ]; then
    echo "📁 Creating templates directory..."
    mkdir -p templates
fi

# Check for environment variables
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  Warning: GROQ_API_KEY not set. LLM features will be limited."
    echo "   Set it with: export GROQ_API_KEY='your_api_key_here'"
fi

echo "🚀 Starting Flask Web Client on port 5000..."
echo "📊 Dashboard will be available at: http://localhost:5000"
$PYTHON_CMD app.py
