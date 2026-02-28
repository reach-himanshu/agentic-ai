"""
Client Onboarding Agent - D365 + Workday specialist.

Owns:
- D365 MCP (client records)
- Workday MCP (billing/time setup)

Inherits from orchestrator:
- Knowledge Hub MCP
- MS Graph MCP
"""
from pathlib import Path
from agents.base import DomainAgent, AgentConfig
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class OnboardingAgent(DomainAgent):
    """
    Client Onboarding domain agent for D365 + Workday operations.
    """
    
    def __init__(self):
        config = AgentConfig.from_yaml(str(CONFIG_PATH))
        super().__init__(config)
        self.d365_mcp = None
        self.workday_mcp = None
    
    async def initialize(self, shared_mcp_registry: dict = None):
        """Load D365 + Workday MCPs (owned) + shared MCPs."""
        await super().initialize(shared_mcp_registry)
        
        # Load owned MCP: D365
        try:
            from mcp_registry.d365 import mcp as d365_mcp
            self.d365_mcp = d365_mcp
            self.mcp_instances.append(d365_mcp)
            logger.info("[OnboardingAgent] Loaded D365 MCP")
        except ImportError as e:
            logger.warning(f"[OnboardingAgent] Could not load D365 MCP: {e}")
        
        # Load owned MCP: Workday
        try:
            from mcp_registry.workday import mcp as workday_mcp
            self.workday_mcp = workday_mcp
            self.mcp_instances.append(workday_mcp)
            logger.info("[OnboardingAgent] Loaded Workday MCP")
        except ImportError as e:
            logger.warning(f"[OnboardingAgent] Could not load Workday MCP: {e}")
        
        # Add shared MCPs
        for name, mcp in self.shared_mcp_registry.items():
            self.mcp_instances.append(mcp)
            logger.info(f"[OnboardingAgent] Added shared MCP: {name}")
        
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
                logger.warning(f"[OnboardingAgent] Error loading tools: {e}")
    
    async def process(self, task: str, context: dict) -> dict:
        """Process a client onboarding request."""
        return {
            "response": None,
            "fallback": True,
            "agent_id": "onboarding",
            "agent_prompt": self.get_system_prompt(),
            "agent_tools": [t.name for t in self.tools],
        }
