"""
IT Support Agent - ServiceNow specialist.

Owns:
- ServiceNow MCP

Inherits from orchestrator:
- Knowledge Hub MCP
- MS Graph MCP
"""
from pathlib import Path
from agents.base import DomainAgent, AgentConfig
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class ITSupportAgent(DomainAgent):
    """
    IT Support domain agent for ServiceNow operations.
    """
    
    def __init__(self):
        config = AgentConfig.from_yaml(str(CONFIG_PATH))
        super().__init__(config)
        self.servicenow_mcp = None
    
    async def initialize(self, shared_mcp_registry: dict = None):
        """Load ServiceNow MCP (owned) + shared MCPs."""
        await super().initialize(shared_mcp_registry)
        
        # Load owned MCP: ServiceNow
        try:
            from mcp_registry.servicenow import mcp as servicenow_mcp
            self.servicenow_mcp = servicenow_mcp
            self.mcp_instances.append(servicenow_mcp)
            logger.info("[ITSupportAgent] Loaded ServiceNow MCP")
        except ImportError as e:
            logger.warning(f"[ITSupportAgent] Could not load ServiceNow MCP: {e}")
        
        # Add shared MCPs
        for name, mcp in self.shared_mcp_registry.items():
            self.mcp_instances.append(mcp)
            logger.info(f"[ITSupportAgent] Added shared MCP: {name}")
        
        await self._load_tools()
    
    async def _load_tools(self):
        """Load tools from MCP servers, filtered by config."""
        allowed_tools = set(self.config.tools)
        
        for mcp_instance in self.mcp_instances:
            try:
                mcp_tools = await mcp_instance.list_tools()
                for tool in mcp_tools:
                    if not allowed_tools or tool.name in allowed_tools:
                        self.tools.append(tool)
            except Exception as e:
                logger.warning(f"[ITSupportAgent] Error loading tools: {e}")
    
    async def process(self, task: str, context: dict) -> dict:
        """Process an IT support request."""
        # TODO: Implement focused AutoGen agent loop
        return {
            "response": None,
            "fallback": True,
            "agent_id": "it_support",
            "agent_prompt": self.get_system_prompt(),
            "agent_tools": [t.name for t in self.tools],
        }
