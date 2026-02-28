"""
HR Agent - Workday specialist.

Owns:
- Workday MCP

Inherits from orchestrator:
- Knowledge Hub MCP
- MS Graph MCP
"""
from pathlib import Path
from agents.base import DomainAgent, AgentConfig
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class HRAgent(DomainAgent):
    """
    HR domain agent for Workday operations.
    """
    
    def __init__(self):
        config = AgentConfig.from_yaml(str(CONFIG_PATH))
        super().__init__(config)
        self.workday_mcp = None
    
    async def initialize(self, shared_mcp_registry: dict = None):
        """Load Workday MCP (owned) + shared MCPs."""
        await super().initialize(shared_mcp_registry)
        
        # Load owned MCP: Workday
        try:
            from mcp_registry.workday import mcp as workday_mcp
            self.workday_mcp = workday_mcp
            self.mcp_instances.append(workday_mcp)
            logger.info("[HRAgent] Loaded Workday MCP")
        except ImportError as e:
            logger.warning(f"[HRAgent] Could not load Workday MCP: {e}")
        
        # Load owned MCP: Time Entry
        try:
            from mcp_registry.time_entry import mcp as time_entry_mcp
            self.mcp_instances.append(time_entry_mcp)
            logger.info("[HRAgent] Loaded Time Entry MCP")
        except ImportError as e:
            logger.warning(f"[HRAgent] Could not load Time Entry MCP: {e}")
        
        # Add shared MCPs
        for name, mcp in self.shared_mcp_registry.items():
            self.mcp_instances.append(mcp)
            logger.info(f"[HRAgent] Added shared MCP: {name}")
        
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
                logger.warning(f"[HRAgent] Error loading tools: {e}")
    
    async def process(self, task: str, context: dict) -> dict:
        """Process an HR request."""
        return {
            "response": None,
            "fallback": True,
            "agent_id": "hr",
            "agent_prompt": self.get_system_prompt(),
            "agent_tools": [t.name for t in self.tools],
        }
