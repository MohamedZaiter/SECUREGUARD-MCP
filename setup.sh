#!/bin/bash
# SecureGuard MCP Setup Script
set -e

echo "🛡️  SecureGuard MCP Setup"
echo "========================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    local version=$($python_cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 7 ]; then
        return 0
    else
        return 1
    fi
}

# Check Python installation
echo "🐍 Checking Python installation..."
PYTHON_CMD=""

if command_exists python3; then
    if check_python_version python3; then
        PYTHON_CMD="python3"
        echo "✅ Found Python 3.7+ at: $(which python3)"
    else
        echo "❌ Python 3.7+ required, found: $(python3 --version)"
        exit 1
    fi
elif command_exists python; then
    if check_python_version python; then
        PYTHON_CMD="python"
        echo "✅ Found Python 3.7+ at: $(which python)"
    else
        echo "❌ Python 3.7+ required, found: $(python --version)"
        exit 1
    fi
else
    echo "❌ Python not found. Please install Python 3.7+ first."
    exit 1
fi

# Check pip
echo "📦 Checking pip installation..."
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo "❌ pip not found. Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $PYTHON_CMD get-pip.py
    rm get-pip.py
fi
echo "✅ pip is available"

# Create project structure
echo "📁 Creating project structure..."
mkdir -p templates
mkdir -p static
mkdir -p logs

# Create .env template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# OpenAI API Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# MCP Configuration
MCP_SERVER_PORT=9002
WEB_SERVER_PORT=5000
EOF
    echo "✅ Created .env template"
else
    echo "ℹ️  .env file already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Dependencies marker
.deps_installed

# OS
.DS_Store
Thumbs.db
EOF
    echo "✅ Created .gitignore"
else
    echo "ℹ️  .gitignore file already exists"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements.txt
    touch .deps_installed
    echo "✅ Dependencies installed successfully"
else
    echo "⚠️  requirements.txt not found. You'll need to install dependencies manually."
fi

# Check required files
echo "🔍 Checking required files..."
missing_files=()

if [ ! -f "mcp_server.py" ]; then
    missing_files+=("mcp_server.py")
fi

if [ ! -f "llm_client.py" ]; then
    missing_files+=("llm_client.py")
fi

if [ ! -f "app.py" ]; then
    missing_files+=("app.py")
fi

if [ ! -f "templates/index.html" ]; then
    missing_files+=("templates/index.html")
fi

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "⚠️  Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "💡 Please ensure all Python files and templates are in place before running."
else
    echo "✅ All required files are present"
fi

# Make shell scripts executable
echo "🔧 Making shell scripts executable..."
for script in start_server.sh start_client.sh start_all.sh; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo "✅ Made $script executable"
    fi
done

# Test MCP server (quick validation)
echo "🧪 Running quick validation..."
if [ -f "mcp_server.py" ] && [ -f "llm_client.py" ]; then
    echo "✅ Core files validated"
else
    echo "⚠️  Some core files are missing"
fi

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   - Set GROQ_API_KEY (required for LLM features)"
echo "   - Set OPENAI_API_KEY (optional alternative)"
echo ""
echo "2. Ensure all project files are in place:"
echo "   - mcp_server.py"
echo "   - llm_client.py" 
echo "   - app.py"
echo "   - templates/index.html"
echo ""
echo "3. Start the system:"
echo "   ./start_all.sh    # Start both services"
echo "   # OR individually:"
echo "   ./start_server.sh # Start MCP server only"
echo "   ./start_client.sh # Start web client only"
echo ""
echo "4. Access the dashboard:"
echo "   📊 Dashboard: http://localhost:5000"
echo "   📡 API Status: http://localhost:5000/api/status"
echo "   🏥 Health Check: http://localhost:5000/api/health"
echo ""
echo "💡 Tips:"
echo "   - Use 'tool: tool_name' for direct tool calls"
echo "   - Check logs/ directory for error details"
echo "   - Run setup.sh again if you encounter issues"
echo ""

# Final environment check
if [ -z "$GROQ_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Remember to set your API keys in .env or export them:"
    echo "   export GROQ_API_KEY='your_groq_key_here'"
    echo ""
fi