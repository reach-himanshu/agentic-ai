"""
Pricing MCP Server.

Provides pricing-specific tools and resources for the Pricing Assistant agent.
"""
import logging
from typing import List, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools import (
    pricing_get_rate_card,
    pricing_get_all_rates,
    pricing_validate_engagement,
    pricing_get_ui_template,
)

logger = logging.getLogger(__name__)


class PricingMCPServer:
    """MCP Server for pricing tools and resources."""
    
    def __init__(self):
        self.server = Server("pricing")
        self._register_tools()
    
    def _register_tools(self):
        """Register all pricing tools with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available pricing tools."""
            return [
                Tool(
                    name="pricing_get_rate_card",
                    description="Get hourly rate for a specific service line and role",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_line": {
                                "type": "string",
                                "enum": ["tax", "aa", "managed_acct", "consulting_snow", "consulting_d365"],
                                "description": "Service line"
                            },
                            "role": {
                                "type": "string",
                                "enum": ["Partner", "Senior Manager", "Manager", "Senior", "Staff"],
                                "description": "Role level"
                            },
                            "geography": {
                                "type": "string",
                                "enum": ["US", "UK", "India"],
                                "description": "Geographic region (default: US)",
                                "default": "US"
                            }
                        },
                        "required": ["service_line", "role"]
                    }
                ),
                Tool(
                    name="pricing_get_all_rates",
                    description="Get all rates for a specific service line",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_line": {
                                "type": "string",
                                "enum": ["tax", "aa", "managed_acct", "consulting_snow", "consulting_d365"],
                                "description": "Service line"
                            }
                        },
                        "required": ["service_line"]
                    }
                ),
                Tool(
                    name="pricing_validate_engagement",
                    description="Validate pricing parameters against business rules",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_line": {
                                "type": "string",
                                "enum": ["tax", "aa", "managed_acct", "consulting_snow", "consulting_d365"],
                                "description": "Service line"
                            },
                            "revenue_model": {
                                "type": "string",
                                "enum": ["tm", "fixed", "milestone", "retainer"],
                                "description": "Revenue model"
                            },
                            "estimated_hours": {
                                "type": "integer",
                                "description": "Estimated hours for engagement"
                            },
                            "target_margin": {
                                "type": "number",
                                "description": "Target margin (0.0-1.0)",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "total_cost": {
                                "type": "number",
                                "description": "Total cost"
                            },
                            "total_price": {
                                "type": "number",
                                "description": "Total price"
                            }
                        },
                        "required": ["service_line", "revenue_model"]
                    }
                ),
                Tool(
                    name="pricing_get_ui_template",
                    description="Get a pre-built UI template (Zero-LLM) for pricing displays",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "template_name": {
                                "type": "string",
                                "enum": ["rate_card_summary", "pricing_breakdown", "approval_request"],
                                "description": "Template name"
                            },
                            "data": {
                                "type": "object",
                                "description": "Optional data to inject into template"
                            }
                        },
                        "required": ["template_name"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "pricing_get_rate_card":
                    result = await pricing_get_rate_card(**arguments)
                elif name == "pricing_get_all_rates":
                    result = await pricing_get_all_rates(**arguments)
                elif name == "pricing_validate_engagement":
                    result = await pricing_validate_engagement(**arguments)
                elif name == "pricing_get_ui_template":
                    result = await pricing_get_ui_template(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(
                    type="text",
                    text=str(result)
                )]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def run(self):
        """Run the MCP server."""
        await self.server.run()


# Create server instance
pricing_server = PricingMCPServer()
