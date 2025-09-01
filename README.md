# SecureGuard Dashboard

A modern security monitoring and analysis platform with AI-powered assistance, built using Flask, MCP (Model Context Protocol), and Groq LLM integration.

![SecureGuard Dashboard ](/home/zaiter/Downloads/secureguard-mcp/client/templates/Screenshot From 2025-09-01 15-27-06.png)

## Features

- **Real-time Security Monitoring**: Track organizations, security cases, and threat signals
- **AI-Powered Assistant**: Chat with an intelligent assistant powered by Groq LLM
- **MCP Integration**: Seamless communication with security data through Model Context Protocol
- **Modern Web Interface**: Responsive dashboard with dark/light theme support
- **Streaming Responses**: Real-time chat experience with streaming API responses
- **RESTful API**: Complete REST API for programmatic access to security data

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │───▶│   Flask App     │───▶│   MCP Server    │
│   (HTML/JS)     │    │   (app.py)      │    │ (mcp_server.py) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Groq LLM      │
                       │   (llm_client)  │
                       └─────────────────┘
```

## Requirements

### Python Dependencies

```bash
pip install flask groq fastmcp httpx mcp
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required for LLM functionality
GROQ_API_KEY=your_groq_api_key_here

# Optional Flask configuration
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
LOG_LEVEL=INFO
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd secureguard-dashboard
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Groq API key
```

### 3. Start MCP Server

```bash
python mcp_server.py
```

The MCP server will start on port 9002 with SSE transport.

### 4. Start Flask Application

```bash
python app.py
```

The web interface will be available at http://localhost:5000

## API Documentation

### Authentication

No authentication is required for the demo. In production, implement proper authentication middleware.

### Endpoints

#### Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "components": {
    "mcp_server": "connected",
    "groq_llm": "available"
  },
  "version": "1.0.0"
}
```

#### Query Assistant
```http
POST /api/query
Content-Type: application/json

{
  "query": "Get security summary"
}
```

Response: Server-Sent Events stream

#### List Tools
```http
GET /api/tools
```

#### System Status
```http
GET /api/status
```

#### Clear Conversation
```http
POST /api/clear
```

### MCP Direct Access

#### Security Summary
```http
GET /api/mcp/summary
```

#### Organizations
```http
GET /api/mcp/organizations
```

#### Security Cases
```http
GET /api/mcp/cases?status=active
```

#### Security Signals
```http
GET /api/mcp/signals?org=OrgA&type=MALWARE
```

## MCP Tools

The MCP server provides the following tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_organizations` | List all monitored organizations | None |
| `get_organization_details` | Get org details | `org_name` (required) |
| `filter_organizations_by_type` | Filter orgs by type | `org_type` (required) |
| `list_cases` | List security cases | `status` (optional) |
| `get_case_details` | Get case details | `case_id` (required) |
| `list_signals` | List security signals | `org_name`, `signal_type` (optional) |
| `get_security_summary` | Get security overview | None |
| `health` | Check server health | None |

### Direct Tool Usage

You can call tools directly in the chat interface:

```
tool: get_security_summary
tool: list_cases status=active
tool: get_organization_details org_name=OrgA
```

## Configuration

### Flask Configuration

Environment variables for Flask app customization:

- `FLASK_SECRET_KEY`: Session encryption key
- `FLASK_DEBUG`: Debug mode (True/False)
- `FLASK_HOST`: Host to bind to (default: 0.0.0.0)
- `FLASK_PORT`: Port to bind to (default: 5000)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### MCP Server Configuration

The MCP server runs on port 9002 by default. To change this, modify the `PORT` variable in `mcp_server.py`.

### LLM Configuration

The system uses Groq's API for LLM functionality. Configure your API key in the `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

## Development

### Project Structure

```
secureguard-dashboard/
├── app.py              # Flask web application
├── llm_client.py       # LLM and MCP client logic
├── mcp_server.py       # MCP server with security tools
├── templates/
│   └── index.html      # Web interface
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md          # This file
```

### Adding New Tools

1. Define your tool function in `mcp_server.py`:

```python
def my_new_tool(param1: str, param2: int = 10) -> Dict[str, Any]:
    """Tool description for documentation."""
    # Your tool logic here
    return {"result": "success"}
```

2. Add it to the tools list in `create_mcp_server()`:

```python
tools = [
    # ... existing tools
    my_new_tool
]
```

3. Update tool descriptions in `llm_client.py`:

```python
self.tool_descriptions = {
    # ... existing descriptions
    "my_new_tool": "Description of what the tool does"
}
```

### Error Handling

The application includes comprehensive error handling:

- **Connection errors**: Graceful degradation when MCP server is unavailable
- **API errors**: Proper error responses with status codes
- **Validation errors**: Input validation and sanitization
- **LLM errors**: Fallback suggestions when LLM is unavailable

### Logging

Logging is configured at the application level. Adjust the `LOG_LEVEL` environment variable:

- `DEBUG`: Detailed debugging information
- `INFO`: General application flow
- `WARNING`: Warning messages
- `ERROR`: Error messages only

## Production Deployment

### Security Considerations

1. **Authentication**: Implement proper user authentication
2. **HTTPS**: Use TLS encryption for production
3. **API Keys**: Secure storage of API keys (use secrets management)
4. **Input Validation**: Additional input sanitization
5. **Rate Limiting**: Implement rate limiting for API endpoints

### Deployment Options

#### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000 9002

CMD ["python", "app.py"]
```

#### Process Management

Use a process manager like `supervisord` or `systemd` to manage both the Flask app and MCP server.

Example `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    command: python mcp_server.py
    ports:
      - "9002:9002"
    environment:
      - LOG_LEVEL=INFO
  
  web-app:
    build: .
    command: python app.py
    ports:
      - "5000:5000"
    depends_on:
      - mcp-server
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
```

## Troubleshooting

### Common Issues

#### MCP Server Connection Failed

```
❌ MCP Server connection failed - check if MCP server is running on port 9002
```

**Solution**: Start the MCP server first:
```bash
python mcp_server.py
```

#### LLM Unavailable

```
⚠️ GROQ_API_KEY not set - LLM responses will be limited
```

**Solution**: Set your Groq API key in the `.env` file.

#### Port Already in Use

```
OSError: [Errno 48] Address already in use
```

**Solution**: Either stop the process using the port or change the port in configuration.

### Debug Mode

Enable debug mode for detailed error messages:

```bash
export FLASK_DEBUG=True
python app.py
```

### Health Checks

Monitor system health using the health endpoints:

```bash
# Quick health check
curl http://localhost:5000/api/health

# Detailed status
curl http://localhost:5000/api/status
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the API documentation
3. Enable debug logging for more details
4. Create an issue in the repository

## Changelog

### v1.0.0
- Initial release
- Flask web interface
- MCP server integration
- Groq LLM support
- Real-time streaming responses
- Dark/light theme support