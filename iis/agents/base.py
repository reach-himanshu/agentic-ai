"""
Base agent class with common utilities.
"""
from typing import Any, Callable
from pydantic import BaseModel
import re


class AgentMessage(BaseModel):
    """A message in the agent conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_call: dict | None = None
    tool_result: dict | None = None
    confirmation: dict | None = None  # For HITL


class BaseAgent:
    """Base class for agents with common utilities."""
    
    def __init__(self, name: str):
        self.name = name
        self.conversation: list[AgentMessage] = []
    
    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to conversation history."""
        msg = AgentMessage(role=role, content=content, **kwargs)
        self.conversation.append(msg)
        return msg
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation = []
    
    def extract_intent(self, user_message: str) -> dict:
        """
        Extract user intent from message.
        For POC, uses simple keyword matching.
        In production, would use LLM for NLU.
        """
        message_lower = user_message.lower()
        
        # Client lookup
        if any(kw in message_lower for kw in ["find", "lookup", "search", "get"]):
            # Try to extract client name/ID
            return {"action": "lookup_client", "raw_query": user_message}
        
        # Stage update
        if any(kw in message_lower for kw in ["update", "change", "move", "stage"]):
            return {"action": "update_stage", "raw_query": user_message}
        
        # Owner assignment
        if any(kw in message_lower for kw in ["assign", "reassign", "owner", "transfer"]):
            return {"action": "assign_owner", "raw_query": user_message}
        
        # Default - general query
        return {"action": "general", "raw_query": user_message}
    
    def extract_client_reference(self, text: str) -> str | None:
        """Extract client name/ID from text."""
        # Common patterns
        patterns = [
            r"(?:for|about|client|company)\s+['\"]?([A-Za-z][A-Za-z0-9\s]+)['\"]?",
            r"acme|global\s*tech|startup",
        ]
        
        text_lower = text.lower()
        
        # Check for known clients
        if "acme" in text_lower:
            return "acme-corp"
        if "global" in text_lower and "tech" in text_lower:
            return "global-tech"
        if "startup" in text_lower:
            return "startup-xyz"
        
        # Try regex patterns
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().lower().replace(" ", "-")
        
        return None
    
    def extract_stage(self, text: str) -> str | None:
        """Extract stage name from text."""
        stages = {
            "prospect": "prospect",
            "qualified": "qualified",
            "negotiation": "negotiation",
            "closed won": "closed_won",
            "closed lost": "closed_lost",
            "won": "closed_won",
            "lost": "closed_lost",
        }
        
        text_lower = text.lower()
        for keyword, stage in stages.items():
            if keyword in text_lower:
                return stage
        
        return None


# ============================================================================
# NEW: Domain Agent Architecture (Modular Agents)
# ============================================================================

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class AgentConfig:
    """Configuration for a domain-specific agent."""
    name: str
    description: str = ""
    prompt_template: str = ""
    owned_mcps: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    pills: list[dict] = field(default_factory=list)
    guardrails_scope: list[str] = field(default_factory=list)
    ui_templates: dict = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "AgentConfig":
        """Load agent config from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


class DomainAgent(ABC):
    """
    Base class for domain-specific agents.
    
    Each domain agent:
    - Owns specific MCP servers (e.g., CRM owns D365)
    - Has a focused system prompt
    - Exposes only relevant tools
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.mcp_instances = []
        self.tools = []
        self.model_client = None
    
    async def initialize(self, shared_mcp_registry: dict = None):
        """
        Initialize the agent with its owned MCPs + shared MCPs.
        
        Args:
            shared_mcp_registry: Dict of shared MCPs from orchestrator (e.g., KB, M365)
        """
        # Subclasses should override to load their owned MCPs
        self.shared_mcp_registry = shared_mcp_registry or {}
    
    @abstractmethod
    async def process(self, task: str, context: dict) -> dict:
        """
        Process a user request.
        
        Args:
            task: The user's message/request
            context: Dict containing user_id, session_id, prior_results, etc.
        
        Returns:
            Dict with 'response', 'manifest' (optional), 'handoff' (optional)
        """
        pass
    
    def get_system_prompt(self) -> str:
        """Get the agent's focused system prompt."""
        return self.config.prompt_template
    
    def get_pills(self) -> list[dict]:
        """Get agent-specific action pills for the UI."""
        return self.config.pills
    
    def get_capabilities(self) -> list[str]:
        """Get list of capabilities for UI display."""
        return self.config.tools
