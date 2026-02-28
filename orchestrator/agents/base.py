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
