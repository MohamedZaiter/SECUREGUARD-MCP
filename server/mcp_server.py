"""
SecureGuard MCP Server

Model Context Protocol server for security monitoring data and operations.
Provides tools for organization management, case tracking, and security analysis.
"""

import json
import datetime
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP

# Mock data for demonstration purposes
# In production, this would connect to real databases/APIs

ORGANIZATIONS = {
    "OrgA": {"type": "technology", "employees": 1500, "risk_level": "medium"},
    "OrgB": {"type": "finance", "employees": 800, "risk_level": "high"},
    "OrgC": {"type": "healthcare", "employees": 2200, "risk_level": "low"},
    "OrgD": {"type": "technology", "employees": 3500, "risk_level": "medium"},
    "OrgE": {"type": "retail", "employees": 1200, "risk_level": "low"}
}

SECURITY_CASES = [
    {
        "id": "CASE001",
        "type": "intrusion",
        "severity": "high",
        "status": "active",
        "org": "OrgB",
        "created_at": "2024-01-10T14:30:00Z",
        "updated_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "CASE002",
        "type": "phishing",
        "severity": "medium",
        "status": "investigating",
        "org": "OrgA",
        "created_at": "2024-01-12T11:15:00Z",
        "updated_at": "2024-01-14T16:45:00Z"
    },
    {
        "id": "CASE003",
        "type": "malware",
        "severity": "low",
        "status": "resolved",
        "org": "OrgC",
        "created_at": "2024-01-08T08:20:00Z",
        "updated_at": "2024-01-13T14:30:00Z"
    },
    {
        "id": "CASE004",
        "type": "data_breach",
        "severity": "critical",
        "status": "active",
        "org": "OrgB",
        "created_at": "2024-01-14T22:15:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": "CASE005",
        "type": "ddos",
        "severity": "medium",
        "status": "mitigating",
        "org": "OrgD",
        "created_at": "2024-01-13T19:45:00Z",
        "updated_at": "2024-01-15T08:00:00Z"
    }
]

SECURITY_SIGNALS = [
    {
        "id": "SIG001",
        "timestamp": "2024-01-15T10:30:00Z",
        "type": "IDS_ALERT",
        "severity": "high",
        "message": "SQL Injection attempt detected on web server",
        "org": "OrgB",
        "source_ip": "192.168.1.50"
    },
    {
        "id": "SIG002",
        "timestamp": "2024-01-15T11:15:00Z",
        "type": "MALWARE",
        "severity": "medium",
        "message": "Malware hash 0x4f3a2b detected on endpoint",
        "org": "OrgA",
        "affected_host": "workstation-42"
    },
    {
        "id": "SIG003",
        "timestamp": "2024-01-15T12:00:00Z",
        "type": "NETWORK",
        "severity": "medium",
        "message": "Unusual traffic pattern detected",
        "org": "OrgD",
        "source_ip": "10.0.1.100"
    },
    {
        "id": "SIG004",
        "timestamp": "2024-01-15T12:30:00Z",
        "type": "EMAIL",
        "severity": "low",
        "message": "Phishing email blocked by security filter",
        "org": "OrgC",
        "sender": "suspicious@external-domain.com"
    }
]

# Tool Functions
def list_organizations() -> List[str]:
    """List all organizations monitored by SecureGuard."""
    return list(ORGANIZATIONS.keys())

def get_organization_details(org_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific organization.
    
    Args:
        org_name: Name of the organization to get details for
        
    Returns:
        Dictionary containing organization details or error message
    """
    if org_name not in ORGANIZATIONS:
        return {"error": f"Organization '{org_name}' not found"}
    
    org_data = ORGANIZATIONS[org_name].copy()
    
    # Add related cases and signals
    related_cases = [case for case in SECURITY_CASES if case["org"] == org_name]
    related_signals = [signal for signal in SECURITY_SIGNALS if signal["org"] == org_name]
    
    org_data.update({
        "name": org_name,
        "active_cases": len([c for c in related_cases if c["status"] == "active"]),
        "total_cases": len(related_cases),
        "recent_signals": len([s for s in related_signals]),
        "last_activity": max([s["timestamp"] for s in related_signals], default="N/A")
    })
    
    return org_data

def filter_organizations_by_type(org_type: str) -> List[Dict[str, Any]]:
    """Filter organizations by their type.
    
    Args:
        org_type: Type of organizations to filter by (e.g., 'technology', 'finance')
        
    Returns:
        List of organizations matching the specified type
    """
    matching_orgs = []
    for name, data in ORGANIZATIONS.items():
        if data["type"].lower() == org_type.lower():
            org_data = data.copy()
            org_data["name"] = name
            matching_orgs.append(org_data)
    
    return matching_orgs

def list_cases(status: str = "all") -> List[Dict[str, Any]]:
    """List security cases, optionally filtered by status.
    
    Args:
        status: Filter by case status ('all', 'active', 'resolved', etc.)
        
    Returns:
        List of security cases matching the criteria
    """
    if status == "all":
        return SECURITY_CASES.copy()
    
    return [case for case in SECURITY_CASES if case["status"] == status]

def get_case_details(case_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific security case.
    
    Args:
        case_id: ID of the case to get details for
        
    Returns:
        Dictionary containing case details or error message
    """
    case = next((c for c in SECURITY_CASES if c["id"] == case_id), None)
    if not case:
        return {"error": f"Case '{case_id}' not found"}
    
    case_details = case.copy()
    
    # Add related signals
    related_signals = [
        signal for signal in SECURITY_SIGNALS 
        if signal["org"] == case["org"] and signal["type"].upper() in case["type"].upper()
    ]
    
    case_details["related_signals"] = len(related_signals)
    case_details["recent_signals"] = related_signals[:3]  # Last 3 signals
    
    return case_details

def list_signals(org_name: str = "all", signal_type: str = "all") -> List[Dict[str, Any]]:
    """List security signals with optional filtering.
    
    Args:
        org_name: Filter by organization name ('all' for no filter)
        signal_type: Filter by signal type ('all' for no filter)
        
    Returns:
        List of security signals matching the criteria
    """
    signals = SECURITY_SIGNALS.copy()
    
    if org_name != "all":
        signals = [s for s in signals if s["org"] == org_name]
    
    if signal_type != "all":
        signals = [s for s in signals if s["type"].lower() == signal_type.lower()]
    
    return signals

def get_security_summary() -> Dict[str, Any]:
    """Get comprehensive security summary with key metrics.
    
    Returns:
        Dictionary containing security overview metrics
    """
    # Calculate metrics
    total_orgs = len(ORGANIZATIONS)
    high_risk_orgs = len([o for o in ORGANIZATIONS.values() if o["risk_level"] == "high"])
    
    active_cases = len([c for c in SECURITY_CASES if c["status"] == "active"])
    critical_cases = len([c for c in SECURITY_CASES if c["severity"] == "critical"])
    
    # Recent signals (last 24 hours for demo)
    recent_signals = len(SECURITY_SIGNALS)  # All signals are "recent" in our demo data
    
    # Calculate risk distribution
    risk_distribution = {}
    for org_data in ORGANIZATIONS.values():
        risk_level = org_data["risk_level"]
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
    
    # Case status distribution
    case_status_distribution = {}
    for case in SECURITY_CASES:
        status = case["status"]
        case_status_distribution[status] = case_status_distribution.get(status, 0) + 1
    
    return {
        "summary": {
            "total_organizations": total_orgs,
            "high_risk_organizations": high_risk_orgs,
            "active_cases": active_cases,
            "critical_cases": critical_cases,
            "recent_signals_24h": recent_signals,
            "last_updated": datetime.datetime.now().isoformat()
        },
        "risk_distribution": risk_distribution,
        "case_status_distribution": case_status_distribution,
        "top_affected_orgs": [
            {"org": "OrgB", "active_cases": 2, "risk_level": "high"},
            {"org": "OrgD", "active_cases": 1, "risk_level": "medium"},
            {"org": "OrgA", "active_cases": 1, "risk_level": "medium"}
        ]
    }

def health() -> Dict[str, Any]:
    """Check the health status of the MCP server and data sources.
    
    Returns:
        Dictionary containing health status information
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "data_sources": {
            "organizations": len(ORGANIZATIONS),
            "security_cases": len(SECURITY_CASES),
            "security_signals": len(SECURITY_SIGNALS)
        },
        "services": {
            "database": "connected",
            "api": "available",
            "monitoring": "active"
        },
        "uptime": "Running since server start"
    }

# Create MCP server instance
def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all tools."""
    tools = [
        list_organizations,
        get_organization_details,
        filter_organizations_by_type,
        list_cases,
        get_case_details,
        list_signals,
        get_security_summary,
        health
    ]
    
    return FastMCP(name="SecureGuard-MCP", tools=tools)

def print_startup_info(port: int) -> None:
    """Print startup information and available tools."""
    tools_info = [
        ("list_organizations", "List all monitored organizations"),
        ("get_organization_details", "Get detailed org information"),
        ("filter_organizations_by_type", "Filter orgs by type"),
        ("list_cases", "List security cases (filterable)"),
        ("get_case_details", "Get specific case details"),
        ("list_signals", "List security signals (filterable)"),
        ("get_security_summary", "Get comprehensive security overview"),
        ("health", "Check server health status")
    ]
    
    print("🚀 Starting SecureGuard MCP Server...")
    print("🔧 Available tools:")
    for tool_name, description in tools_info:
        print(f"   - {tool_name}: {description}")
    
    print(f"\n🌐 Server running at http://0.0.0.0:{port}")
    print("🔡 MCP Endpoint: /sse")
    print("🏥 Health check: /health")
    print("🛑 Press Ctrl+C to stop\n")

if __name__ == "__main__":
    # Server configuration
    PORT = 9002
    HOST = "0.0.0.0"
    
    # Create MCP server
    mcp_server = create_mcp_server()
    
    # Print startup information
    print_startup_info(PORT)
    
    # Start the server with SSE transport
    try:
        mcp_server.run(transport="sse", host=HOST, port=PORT)
    except KeyboardInterrupt:
        print("\n🛑 SecureGuard MCP Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")