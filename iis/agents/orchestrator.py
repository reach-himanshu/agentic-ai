"""
Orchestrator - Control plane for Ops IQ agent architecture.

Responsibilities:
- Session/context management
- Intent routing to domain agents
- HITL checkpoints
- Security guardrails
- Agent selection based on entitlements
"""
from typing import Optional, Callable
import logging
import asyncio

from agents.entitlements import (
    get_available_agents,
    has_app_access,
    get_agent_catalog,
    is_entitled_to_agent,
)

logger = logging.getLogger(__name__)


# Shared MCPs owned by orchestrator (available to all agents)
SHARED_MCPS = ["knowledge_hub", "msgraph"]

# Keyword-based routing hints
ROUTING_KEYWORDS = {
    "sales": ["client", "account", "opportunity", "crm", "d365", "dynamics", "pipeline", "lead", "cpq", "quote"],
    "onboarding": ["onboarding", "new client", "client setup", "client ambassador"],
    "it_support": ["ticket", "incident", "servicenow", "snow", "it support", "help desk", "password", "access"],
    "hr": ["time entry", "timesheet", "payroll", "pto", "vacation", "workday", "benefits", "hr"],
    "pricing_assistant": ["pricing", "price", "quote", "proposal", "sow", "statement of work", "scoping", "estimate", "budget", "cost"],
}


class Orchestrator:
    """
    Control Plane for Ops IQ.
    
    Manages session state, routes requests to domain agents,
    and handles cross-cutting concerns like HITL and security.
    """
    
    def __init__(self):
        self.domain_agents = {}  # Lazy-loaded domain agents
        self.shared_mcp_registry = {}  # Shared MCPs (KB, M365)
        self.session_context = {}
        self.pending_hitl = None
        self.user_roles = []
        self._initialized = False
    
    async def initialize(self):
        """Initialize shared MCPs for all agents."""
        if self._initialized:
            return
        
        try:
            from mcp_registry.knowledge_hub import mcp as kb_mcp
            self.shared_mcp_registry["knowledge_hub"] = kb_mcp
            logger.info("[Orchestrator] Loaded knowledge_hub MCP")
        except ImportError as e:
            logger.warning(f"[Orchestrator] Could not load knowledge_hub: {e}")
        
        try:
            from mcp_registry.msgraph import mcp as msgraph_mcp
            self.shared_mcp_registry["msgraph"] = msgraph_mcp
            logger.info("[Orchestrator] Loaded msgraph MCP")
        except ImportError as e:
            logger.warning(f"[Orchestrator] Could not load msgraph: {e}")
        
        try:
            from mcp_servers.pricing import pricing_server
            self.shared_mcp_registry["pricing"] = pricing_server
            logger.info("[Orchestrator] Loaded pricing MCP")
        except ImportError as e:
            logger.warning(f"[Orchestrator] Could not load pricing: {e}")
        
        self._initialized = True
    
    def set_user_context(self, roles: list[str], user_id: str = None, email: str = None):
        """Set user context from JWT token."""
        self.user_roles = roles
        self.session_context["user_id"] = user_id
        self.session_context["email"] = email
        logger.info(f"[Orchestrator] User context set: roles={roles}")
    
    def route_to_agent(self, message: str, active_area: str = None) -> Optional[str]:
        """
        Route a message to the appropriate domain agent.
        
        Args:
            message: User's message
            active_area: Explicit area selection (overrides auto-routing)
            
        Returns:
            Agent ID or None if no match
        """
        available = get_available_agents(self.user_roles)
        
        if not available:
            logger.warning("[Orchestrator] User has no entitled agents")
            return None
        
        # Explicit area selection takes priority
        if active_area:
            agent_id = self._area_to_agent(active_area)
            if agent_id and agent_id in available:
                return agent_id
        
        # Keyword-based routing within entitled agents
        msg_lower = message.lower()
        for agent_id, keywords in ROUTING_KEYWORDS.items():
            if agent_id in available:
                if any(kw in msg_lower for kw in keywords):
                    logger.info(f"[Orchestrator] Routed to {agent_id} via keyword match")
                    return agent_id
        
        # Default: return first available agent
        default_agent = available[0] if available else None
        logger.info(f"[Orchestrator] Default routing to {default_agent}")
        return default_agent
    
    def _area_to_agent(self, area: str) -> Optional[str]:
        """Map UI area selection to agent ID."""
        area_map = {
            "Dynamics 365": "sales",
            "CRM": "sales",
            "CPQ": "sales",
            "ServiceNow": "it_support",
            "IT Support": "it_support",
            "Workday": "hr",
            "HR": "hr",
            "Client Onboarding": "onboarding",
            "pricing_assistant": "pricing_assistant",  # Pricing Assistant wizard
            "Knowledge Hub": None,  # Handled by shared MCP
        }
        return area_map.get(area)
    
    async def get_agent(self, agent_id: str):
        """
        Get or create a domain agent instance.
        
        Uses lazy loading - agents are only instantiated when needed.
        """
        if agent_id in self.domain_agents:
            return self.domain_agents[agent_id]
        
        # Lazy import to avoid circular dependencies
        agent = await self._create_agent(agent_id)
        if agent:
            await agent.initialize(self.shared_mcp_registry)
            self.domain_agents[agent_id] = agent
        
        return agent
    
    async def _create_agent(self, agent_id: str):
        """Factory method to create domain agents."""
        try:
            if agent_id == "sales":
                from agents.domains.sales.agent import SalesAgent
                return SalesAgent()
            elif agent_id == "onboarding":
                from agents.domains.onboarding.agent import OnboardingAgent
                return OnboardingAgent()
            elif agent_id == "it_support":
                from agents.domains.it_support.agent import ITSupportAgent
                return ITSupportAgent()
            elif agent_id == "hr":
                from agents.domains.hr.agent import HRAgent
                return HRAgent()
            elif agent_id == "pricing_assistant":
                from agents.domains.pricing_assistant.agent import PricingAssistantAgent
                return PricingAssistantAgent()
        except ImportError as e:
            logger.warning(f"[Orchestrator] Could not load agent {agent_id}: {e}")
        
        return None
    
    async def process_message(
        self,
        message: str,
        active_area: str = None,
        session_id: str = "unknown",
        on_step: callable = None,
        context: dict = None
    ) -> dict:
        """
        Process a user message and route to the appropriate agent.
        
        Args:
            message: User's message
            active_area: Optional area hint (e.g., 'sales', 'onboarding')
            session_id: Session identifier for state management
            on_step: Optional callback for progress updates
            context: Optional additional context (e.g., form values, action type)
        
        Returns:
            Response dict with 'response', 'manifest', etc.
        """
        # Ensure orchestrator is initialized
        await self.initialize()
        
        # Check app access
        if not has_app_access(self.user_roles):
            return {
                "response": "You don't have access to Ops IQ. Please contact your administrator.",
                "error": True,
            }
        
        # Route to appropriate agent
        agent_id = self.route_to_agent(message, active_area)
        
        if not agent_id:
            return {
                "response": "I couldn't determine which agent to use. Please select an area or rephrase your request.",
                "pills": self._get_area_pills(),
            }
        
        # Check entitlement
        if not is_entitled_to_agent(self.user_roles, agent_id):
            return {
                "response": f"You don't have access to the {agent_id} agent.",
                "error": True,
            }
        
        # Get agent and process
        agent = await self.get_agent(agent_id)
        logger.info(f"[Orchestrator] get_agent returned: {agent is not None}, type: {type(agent).__name__ if agent else 'None'}")
        
        if not agent:
            # Fallback: Agent not yet implemented, use legacy flow
            return {
                "response": None,  # Signal to use legacy planner
                "fallback": True,
                "agent_id": agent_id,
            }
        
        # Process through domain agent
        agent_context = {
            "session_id": session_id,
            "user_id": self.session_context.get("user_id"),
            "email": self.session_context.get("email"),
            "roles": self.user_roles,
        }
        
        # Merge additional context if provided (e.g., form values)
        if context:
            agent_context.update(context)        
        # Call agent.process()
        logger.info(f"[Orchestrator] Calling agent.process() with message='{message}', context={agent_context}")
        result = await agent.process(message, agent_context)
        logger.info(f"[Orchestrator] agent.process() returned: {result}")
        
        # Return both result and updated context (agent may have modified it)
        return {
            "result": result,
            "context": agent_context  # Return updated context with wizard_state
        }
    
    def _get_area_pills(self) -> list[dict]:
        """Get pills for area selection."""
        return [
            {"label": "CRM / Sales", "action": "area", "value": "Dynamics 365"},
            {"label": "IT Support", "action": "area", "value": "ServiceNow"},
            {"label": "HR / Workday", "action": "area", "value": "Workday"},
            {"label": "Knowledge Hub", "action": "area", "value": "Knowledge Hub"},
        ]
    
    def get_agent_catalog_for_user(self) -> dict:
        """Get the agent catalog filtered by user's entitlements."""
        return get_agent_catalog(self.user_roles)
