"""
SecureGuard Web Interface - Flask Application

A security monitoring dashboard with MCP integration and LLM-powered assistant.
"""

import os
import uuid
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

from flask import Flask, render_template, request, jsonify, session, Response

from llm_client import LLMClient

# Configuration
class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Application setup
app = Flask(__name__)
app.config.from_object(Config)

# Logging configuration
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
llm_client = LLMClient()
executor = ThreadPoolExecutor(max_workers=4)

# Utility functions
def run_async(coro):
    """Run async function safely in sync context."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def create_error_response(message: str, status_code: int = 500):
    """Create standardized error response."""
    return jsonify({"error": message, "status": "error"}), status_code

def create_success_response(data: dict = None, message: str = "success"):
    """Create standardized success response."""
    response = {"status": message}
    if data:
        response.update(data)
    return jsonify(response)

# Routes
@app.route("/")
def index():
    """Main dashboard page."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    
    # Check MCP connection status
    mcp_connected = False
    try:
        future = executor.submit(run_async, llm_client.mcp_client.health_check())
        mcp_connected = future.result(timeout=5)
    except Exception as e:
        logger.warning(f"MCP connection check failed: {e}")
    
    return render_template("index.html", mcp_connected=mcp_connected)

@app.route("/api/query", methods=["POST"])
def handle_query():
    """Handle user queries with streaming support."""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data", 400)
        
        query = data.get("query", "").strip()
        if not query:
            return create_error_response("Query cannot be empty", 400)
        
        session_id = session.get("session_id", str(uuid.uuid4()))
        
        def stream():
            try:
                async def async_stream():
                    async for chunk in llm_client.process_query_streaming(query, session_id):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                
                for chunk in run_async(async_stream()):
                    yield chunk
            except Exception as e:
                logger.error(f"Error in query streaming: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"
                yield "data: [DONE]\n\n"
        
        return Response(
            stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        logger.error(f"Error handling query: {e}", exc_info=True)
        return create_error_response(str(e))

@app.route("/api/tools", methods=["GET"])
def list_tools():
    """List available MCP tools."""
    try:
        tools = run_async(llm_client.get_available_tools())
        return create_success_response({"tools": tools})
    except Exception as e:
        logger.error(f"Error fetching tools: {e}", exc_info=True)
        return create_error_response(
            f"Failed to fetch tools: {str(e)}", 500
        )

@app.route("/api/health", methods=["GET"])
def health_check():
    """Application health check."""
    try:
        mcp_connected = run_async(llm_client.mcp_client.health_check())
        groq_available = llm_client.groq_client is not None
        
        status = "healthy" if mcp_connected and groq_available else "degraded"
        
        return jsonify({
            "status": status,
            "components": {
                "mcp_server": "connected" if mcp_connected else "disconnected",
                "groq_llm": "available" if groq_available else "unavailable"
            },
            "version": "1.0.0",
            "timestamp": app.config.get('startup_time')
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return create_error_response(f"Health check failed: {str(e)}")

@app.route("/api/status", methods=["GET"])
def detailed_status():
    """Get detailed system status."""
    try:
        mcp_connected = run_async(llm_client.mcp_client.health_check())
        available_tools = run_async(llm_client.get_available_tools()) if mcp_connected else []
        
        return jsonify({
            "flask_status": "running",
            "mcp_server": {
                "connected": mcp_connected,
                "url": llm_client.mcp_client.base_url,
                "tools_count": len(available_tools),
                "available_tools": available_tools
            },
            "groq_llm": {
                "available": llm_client.groq_client is not None,
                "api_key_configured": bool(os.getenv("GROQ_API_KEY"))
            },
            "session_info": {
                "active_conversations": len(llm_client.conversations),
                "current_session": session.get("session_id")
            }
        })
    except Exception as e:
        logger.error(f"Error getting detailed status: {e}", exc_info=True)
        return create_error_response(str(e))

@app.route("/api/clear", methods=["POST"])
def clear_conversation():
    """Clear conversation history."""
    try:
        session_id = session.get("session_id")
        if session_id:
            llm_client.clear_conversation(session_id)
        return create_success_response(message="cleared")
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}", exc_info=True)
        return create_error_response(str(e))

# MCP Direct Endpoints
def call_mcp_tool(tool_name: str, **kwargs):
    """Helper function to call MCP tools directly."""
    try:
        if not run_async(llm_client.mcp_client.health_check()):
            return {"error": "MCP server not connected"}, 503
        
        result = run_async(llm_client.mcp_client.call_tool(tool_name, **kwargs))
        return result, 200
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}, 500

@app.route("/api/mcp/summary", methods=["GET"])
def mcp_summary():
    """Get security summary via MCP."""
    result, status = call_mcp_tool("get_security_summary")
    return jsonify(result), status

@app.route("/api/mcp/organizations", methods=["GET"])
def mcp_organizations():
    """List organizations via MCP."""
    result, status = call_mcp_tool("list_organizations")
    return jsonify(result), status

@app.route("/api/mcp/cases", methods=["GET"])
def mcp_cases():
    """List security cases via MCP."""
    status_filter = request.args.get("status", "all")
    result, status = call_mcp_tool("list_cases", status=status_filter)
    return jsonify(result), status

@app.route("/api/mcp/signals", methods=["GET"])
def mcp_signals():
    """List security signals via MCP."""
    org_name = request.args.get("org", "all")
    signal_type = request.args.get("type", "all")
    result, status = call_mcp_tool("list_signals", org_name=org_name, signal_type=signal_type)
    return jsonify(result), status

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return create_error_response("Endpoint not found", 404)

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return create_error_response("Internal server error", 500)

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle uncaught exceptions."""
    logger.error(f"Uncaught exception: {e}", exc_info=True)
    return create_error_response("An unexpected error occurred", 500)

# System initialization
def initialize_system():
    """Initialize and validate system components."""
    print("🛡️  Starting SecureGuard Web Interface...")
    print(f"🌐 Web server at http://{Config.HOST}:{Config.PORT}")
    print("🔧 Ensure MCP server is running on port 9002 (SSE transport)")
    
    # Test MCP connection
    try:
        mcp_connected = run_async(llm_client.mcp_client.health_check())
        if mcp_connected:
            print("✅ MCP Server connection successful")
            try:
                tools = run_async(llm_client.get_available_tools())
                tools_display = ', '.join(tools[:5])
                if len(tools) > 5:
                    tools_display += '...'
                print(f"🔧 {len(tools)} MCP tools available: {tools_display}")
            except Exception as e:
                logger.warning(f"Could not fetch MCP tools list: {e}")
        else:
            print("❌ MCP Server connection failed - check if MCP server is running on port 9002")
    except Exception as e:
        logger.error(f"Error initializing MCP connection: {e}")
        print("❌ MCP Server initialization failed")
    
    # Test Groq LLM
    if llm_client.groq_client:
        print("✅ Groq LLM client initialized")
    else:
        print("⚠️ GROQ_API_KEY not set - LLM responses will be limited")
    
    # Store startup time
    from datetime import datetime
    app.config['startup_time'] = datetime.utcnow().isoformat()
    
    print("\n" + "="*50)
    print("🚀 SecureGuard is ready!")
    print(f"📊 Dashboard: http://{Config.HOST}:{Config.PORT}")
    print(f"📍 API Status: http://{Config.HOST}:{Config.PORT}/api/status")
    print(f"🏥 Health Check: http://{Config.HOST}:{Config.PORT}/api/health")
    print("="*50 + "\n")

if __name__ == "__main__":
    initialize_system()
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT,
        threaded=True
    )