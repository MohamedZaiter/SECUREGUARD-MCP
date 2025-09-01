"""
SecureGuard LLM Client

Handles communication with Groq LLM and MCP server for security monitoring queries.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator

import httpx
from groq import Groq
from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)

class SecureGuardMCPClient:
    """Client for SecureGuard MCP server communication."""
    
    def __init__(self, base_url: str = "http://localhost:9002/sse"):
        self.base_url = base_url
        self.connected = False
        self._patch_httpx()
    
    def _patch_httpx(self) -> None:
        """Patch httpx to handle redirects properly for SSE."""
        original_request = httpx.AsyncClient.request
        
        async def patched_request(self, method, url, *args, **kwargs):
            kwargs.setdefault("follow_redirects", True)
            return await original_request(self, method, url, *args, **kwargs)
        
        httpx.AsyncClient.request = patched_request
    
    async def _with_session(self, func):
        """Execute function within MCP session context."""
        try:
            async with sse_client(url=self.base_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await func(session)
        except Exception as e:
            logger.error(f"MCP operation failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check MCP server health status."""
        try:
            async def check_health(session):
                await session.list_tools()
                return True
            
            return await self._with_session(check_health)
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        try:
            async def get_tools(session):
                tools_response = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools_response.tools
                ]
            
            return await self._with_session(get_tools)
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        try:
            async def execute_tool(session):
                result = await session.call_tool(tool_name, arguments=kwargs or {})
                return self._extract_content(result)
            
            return await self._with_session(execute_tool)
        except Exception as e:
            error_msg = f"Failed to call tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def _extract_content(self, result) -> Dict[str, Any]:
        """Extract content from MCP tool result."""
        if hasattr(result, 'content') and result.content:
            content_item = result.content[0]
            
            if hasattr(content_item, 'text'):
                try:
                    return json.loads(content_item.text)
                except json.JSONDecodeError:
                    return {"result": content_item.text}
            
            if hasattr(content_item, 'data'):
                return content_item.data
        
        # Fallback handling
        if hasattr(result, 'data'):
            return result.data
        
        return result if isinstance(result, dict) else {"result": str(result)}


class LLMClient:
    """Main client for handling LLM and MCP interactions."""
    
    def __init__(self):
        self.groq_client = self._initialize_groq()
        self.mcp_client = SecureGuardMCPClient()
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.tool_descriptions = self._get_tool_descriptions()
    
    def _initialize_groq(self) -> Optional[Groq]:
        """Initialize Groq client if API key is available."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                return Groq(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        return None
    
    def _get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions for available tools."""
        return {
            "list_organizations": "List all organizations monitored by SecureGuard",
            "get_organization_details": "Get detailed info about a specific organization",
            "filter_organizations_by_type": "Filter organizations by type",
            "list_cases": "List security cases. Optional parameter: status (e.g., 'active', 'resolved')",
            "get_case_details": "Get details for a case. Required parameter: case_id (e.g., 'CASE001')",
            "list_signals": "List security signals. Optional parameters: org_name (e.g., 'OrgA'), signal_type (e.g., 'MALWARE')",
            "get_security_summary": "Get a comprehensive security summary with key metrics",
            "health": "Check the health status of the MCP server"
        }
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        try:
            tools = await self.mcp_client.list_tools()
            if tools:
                return [tool['name'] for tool in tools if 'name' in tool]
            return list(self.tool_descriptions.keys())
        except Exception as e:
            logger.error(f"Error getting available tools: {str(e)}")
            return list(self.tool_descriptions.keys())
    
    def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        self.conversations.pop(session_id, None)
    
    def _get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        return self.conversations.setdefault(session_id, [])
    
    def _add_to_conversation(self, session_id: str, role: str, content: str) -> None:
        """Add message to conversation history."""
        history = self._get_conversation_history(session_id)
        history.append({"role": role, "content": content})
        
        # Keep only last 20 messages to prevent token overflow
        if len(history) > 20:
            self.conversations[session_id] = history[-20:]
    
    def _get_tool_suggestions(self, query: str) -> List[str]:
        """Get tool suggestions based on query content."""
        query_lower = query.lower()
        suggestions = []
        
        suggestion_map = {
            ("summary", "overview", "status", "metrics"): "tool: get_security_summary",
            ("organization", "org", "company"): {
                ("list", "all"): "tool: list_organizations",
                ("details", "info", "about"): "tool: get_organization_details org_name=OrgA"
            },
            ("case", "incident", "security case"): {
                ("active",): "tool: list_cases status=active",
                ("details", "info"): "tool: get_case_details case_id=CASE001",
                "default": "tool: list_cases"
            },
            ("signal", "alert", "detection"): "tool: list_signals",
            ("health", "check", "status"): "tool: health"
        }
        
        for keywords, action in suggestion_map.items():
            if any(word in query_lower for word in keywords):
                if isinstance(action, dict):
                    for sub_keywords, sub_action in action.items():
                        if sub_keywords != "default" and any(word in query_lower for word in sub_keywords):
                            suggestions.append(sub_action)
                            break
                    else:
                        if "default" in action:
                            suggestions.append(action["default"])
                else:
                    suggestions.append(action)
        
        return suggestions
    
    async def process_query_streaming(self, query: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process query and return streaming response."""
        self._add_to_conversation(session_id, "user", query)
        
        # Handle direct tool calls
        if query.strip().lower().startswith('tool:'):
            async for chunk in self._handle_tool_query(query):
                yield chunk
        else:
            async for chunk in self._handle_llm_query(query, session_id):
                yield chunk
    
    async def _handle_tool_query(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle direct tool execution queries."""
        try:
            # Parse tool command
            parts = query[len('tool:'):].strip().split(maxsplit=1)
            tool_name = parts[0].strip()
            
            # Parse parameters
            kwargs = {}
            if len(parts) > 1:
                param_str = parts[1].strip()
                for param in param_str.split():
                    if '=' in param:
                        key, value = param.split('=', 1)
                        kwargs[key.strip()] = value.strip()
            
            # Execute tool
            result = await self.mcp_client.call_tool(tool_name, **kwargs)
            response_text = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
            
            # Stream response in chunks
            chunk_size = 100
            for i in range(0, len(response_text), chunk_size):
                yield {
                    "response": response_text[i:i+chunk_size],
                    "type": "tool_response",
                    "done": False
                }
            
            yield {"response": "", "type": "tool_response", "done": True}
            
        except Exception as e:
            yield {
                "response": f"Error executing tool: {str(e)}",
                "type": "error",
                "done": True
            }
    
    async def _handle_llm_query(self, query: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle LLM-powered queries."""
        if not self.groq_client:
            suggestions = self._get_tool_suggestions(query)
            error_msg = "GROQ_API_KEY not set or LLM unavailable."
            if suggestions:
                error_msg += "\n\nTry these direct tool calls:\n" + "\n".join(f"• {s}" for s in suggestions)
            
            yield {"response": error_msg, "type": "error", "done": True}
            return
        
        try:
            # Prepare conversation context
            messages = self._prepare_messages(session_id)
            
            # Get LLM response
            response = self.groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=False
            )
            
            llm_response = response.choices[0].message.content
            self._add_to_conversation(session_id, "assistant", llm_response)
            
            # Stream response in chunks
            chunk_size = 100
            for i in range(0, len(llm_response), chunk_size):
                yield {
                    "response": llm_response[i:i+chunk_size],
                    "type": "llm_response",
                    "done": False
                }
            
            yield {"response": "", "type": "llm_response", "done": True}
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            suggestions = self._get_tool_suggestions(query)
            error_msg = f"LLM Error: {str(e)}"
            if suggestions:
                error_msg += "\n\nTry these direct tool calls:\n" + "\n".join(f"• {s}" for s in suggestions)
            
            yield {"response": error_msg, "type": "error", "done": True}
    
    def _prepare_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Prepare messages for LLM with system context."""
        available_tools = list(self.tool_descriptions.keys())
        tool_context = "\n".join([
            f"- {name}: {self.tool_descriptions.get(name, 'No description')}"
            for name in available_tools
        ])
        
        system_message = {
            "role": "system",
            "content": f"""You are a helpful SecureGuard security monitoring assistant.

Available tools:
{tool_context}

You can help users understand their security posture, analyze cases, and manage organizations.
For direct tool access, users can type 'tool: <tool_name> [parameters]'."""
        }
        
        conversation_history = self._get_conversation_history(session_id)
        return [system_message] + conversation_history