#!/bin/bash
# SecureGuard Complete System Startup Script
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display header
show_header() {
    echo -e "\n${GREEN}🛡️  =============================${NC}"
    echo -e "${GREEN}     SecureGuard MCP System     ${NC}"
    echo -e "${GREEN}=============================${NC}\n"
}

# Function to display error messages
error_exit() {
    echo -e "${RED}❌ $1${NC}" >&2
    exit 1
}

# Function to check if a program is running
is_running() {
    if ps -p $1 > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down SecureGuard...${NC}"
    
    if [ ! -z "$MCP_PID" ] && is_running $MCP_PID; then
        echo -n "🔴 Stopping MCP Server (PID: $MCP_PID)... "
        kill $MCP_PID 2>/dev/null || true
        echo -e "${GREEN}Done${NC}"
    fi
    
    if [ ! -z "$WEB_PID" ] && is_running $WEB_PID; then
        echo -n "🔴 Stopping Web Client (PID: $WEB_PID)... "
        kill $WEB_PID 2>/dev/null || true
        echo -e "${GREEN}Done${NC}"
    fi
    
    echo -e "\n👋 SecureGuard system has been stopped."
    exit 0
}

# Show header
show_header

# Check Python installation
if ! command -v python3 &>/dev/null; then
    error_exit "Python 3.7+ is required but not installed. Please install it and try again."
fi

# Verify Python version
PYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
if [[ "$(printf '%s\n' "3.7" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.7" ]]; then
    error_exit "Python 3.7 or higher is required. Found Python $PYTHON_VERSION"
fi

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${YELLOW}🚀 Starting SecureGuard MCP System...${NC}"

# Start MCP Server
echo -e "\n${YELLOW}🛡️  Starting MCP Server...${NC}"
cd "$(dirname "$0")/server"
if [ -f "start_server.sh" ]; then
    chmod +x start_server.sh
    ./start_server.sh &
    MCP_PID=$!
    echo -e "✅ ${GREEN}MCP Server started (PID: $MCP_PID)${NC}"
else
    error_exit "MCP Server start script not found"
fi

# Give MCP server a moment to start
sleep 2

# Start Web Client
echo -e "\n${YELLOW}🌐 Starting Web Client...${NC}"
cd "$(dirname "$0")/client"
if [ -f "start_client.sh" ]; then
    chmod +x start_client.sh
    ./start_client.sh &
    WEB_PID=$!
    echo -e "✅ ${GREEN}Web Client started (PID: $WEB_PID)${NC}"
else
    error_exit "Web Client start script not found"
fi

echo -e "\n${GREEN}✅ SecureGuard system is now running!${NC}"
echo -e "- MCP Server: ${GREEN}http://localhost:9002${NC}"
echo -e "- Web Client: ${GREEN}http://localhost:5000${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop the system${NC}"

# Keep the script running and monitor processes
while true; do
    if [ ! -z "$MCP_PID" ] && ! is_running $MCP_PID; then
        echo -e "${RED}❌ MCP Server (PID: $MCP_PID) has stopped unexpectedly${NC}"
        cleanup
    fi
    
    if [ ! -z "$WEB_PID" ] && ! is_running $WEB_PID; then
        echo -e "${RED}❌ Web Client (PID: $WEB_PID) has stopped unexpectedly${NC}"
        cleanup
    fi
    
    sleep 5
done
if [ ! -f ".deps_installed" ]; then
    echo "📦 Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        touch .deps_installed
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check required files
if [ ! -f "mcp_server.py" ]; then
    echo "❌ Error: mcp_server.py not found"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found"
    exit 1
fi

# Create templates directory if it doesn't exist
if [ ! -d "templates" ]; then
    echo "📁 Creating templates directory..."
    mkdir -p templates
fi

# Check for environment variables
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  Warning: GROQ_API_KEY not set. LLM features will be limited."
    echo "   Set it with: export GROQ_API_KEY='your_api_key_here'"
    echo ""
fi

echo "🚀 Starting MCP Server..."
$PYTHON_CMD mcp_server.py &
MCP_PID=$!

# Wait a moment for MCP server to start
echo "⏳ Waiting for MCP Server to initialize..."
sleep 3

# Check if MCP server is still running
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo "❌ MCP Server failed to start"
    exit 1
fi

echo "✅ MCP Server started successfully (PID: $MCP_PID)"
echo ""

echo "🌐 Starting Web Client..."
$PYTHON_CMD app.py &
WEB_PID=$!

# Wait a moment for web server to start
echo "⏳ Waiting for Web Client to initialize..."
sleep 2

# Check if web server is still running
if ! kill -0 $WEB_PID 2>/dev/null; then
    echo "❌ Web Client failed to start"
    kill $MCP_PID 2>/dev/null
    exit 1
fi

echo "✅ Web Client started successfully (PID: $WEB_PID)"
echo ""
echo "🎉 SecureGuard is now running!"
echo "📊 Dashboard: http://localhost:5000"
echo "🔧 MCP Server: http://localhost:9002"
echo "📡 API Status: http://localhost:5000/api/status"
echo ""
echo "💡 Tip: Use Ctrl+C to stop both services"
echo ""

# Wait for user to stop the services
wait