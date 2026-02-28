"""
Sales Agent - Dynamics 365 CRM + CPQ specialist.

Owns:
- D365 MCP (primary)
- CPQ MCP (future)

Inherits from orchestrator:
- Knowledge Hub MCP
- MS Graph MCP
"""
from pathlib import Path
from agents.base import DomainAgent, AgentConfig
import logging

logger = logging.getLogger(__name__)

# Path to config relative to this file
CONFIG_PATH = Path(__file__).parent / "config.yaml"


class SalesAgent(DomainAgent):
    """
    Sales domain agent for D365 CRM operations.
    """
    
    def __init__(self):
        config = AgentConfig.from_yaml(str(CONFIG_PATH))
        super().__init__(config)
        self.d365_mcp = None
    
    async def initialize(self, shared_mcp_registry: dict = None):
        """Load D365 MCP (owned) + shared MCPs."""
        await super().initialize(shared_mcp_registry)
        
        # Load owned MCP: D365
        try:
            from mcp_registry.d365 import mcp as d365_mcp
            self.d365_mcp = d365_mcp
            self.mcp_instances.append(d365_mcp)
            logger.info("[SalesAgent] Loaded D365 MCP")
        except ImportError as e:
            logger.warning(f"[SalesAgent] Could not load D365 MCP: {e}")
        
        # Add shared MCPs (KB, M365)
        for name, mcp in self.shared_mcp_registry.items():
            self.mcp_instances.append(mcp)
            logger.info(f"[SalesAgent] Added shared MCP: {name}")
        
        # Load tools from MCP instances
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
                        logger.debug(f"[SalesAgent] Loaded tool: {tool.name}")
            except Exception as e:
                logger.warning(f"[SalesAgent] Error loading tools: {e}")
    
    async def process(self, task: str, context: dict) -> dict:
        """
        Process a CRM-related request.
        
        For now, returns a fallback to use legacy planner.
        Future: Implement full agent loop with AutoGen.
        """
        # TODO: Implement focused AutoGen agent loop
        # For now, signal to orchestrator to use legacy flow
        return {
            "response": None,
            "fallback": True,
            "agent_id": "sales",
            "agent_prompt": self.get_system_prompt(),
            "agent_tools": [t.name for t in self.tools],
        }
