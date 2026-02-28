"""
Prompt Manager - Loads and caches prompt templates from YAML files.

This module provides centralized management of LLM prompts, allowing
configuration changes without code modifications.
"""
import os
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """Represents a loaded prompt template."""
    name: str
    version: str
    description: str
    template: str
    variables: list[str]
    
    def render(self, **kwargs) -> str:
        """Render the template with provided variables."""
        result = self.template
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        return result


class PromptManager:
    """
    Manages LLM prompt templates loaded from YAML files.
    
    Features:
    - Lazy loading with caching
    - Hot-reload capability
    - Template variable substitution
    """
    
    _instance: Optional['PromptManager'] = None
    
    def __init__(self, prompts_dir: str = None):
        """Initialize the PromptManager with a prompts directory."""
        if prompts_dir is None:
            # Default to iis/prompts relative to this file's location
            base_dir = Path(__file__).parent.parent
            prompts_dir = base_dir / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, PromptTemplate] = {}
        self._loaded = False
        
        logger.info(f"[PromptManager] Initialized with directory: {self.prompts_dir}")
    
    @classmethod
    def get_instance(cls) -> 'PromptManager':
        """Get the singleton instance of PromptManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Load a single prompt from its YAML file."""
        file_path = self.prompts_dir / f"{name}.yaml"
        
        if not file_path.exists():
            logger.warning(f"[PromptManager] Prompt file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            template = PromptTemplate(
                name=data.get('name', name),
                version=data.get('version', '1.0'),
                description=data.get('description', ''),
                template=data.get('template', ''),
                variables=data.get('variables', [])
            )
            
            logger.debug(f"[PromptManager] Loaded prompt: {name} v{template.version}")
            return template
            
        except Exception as e:
            logger.error(f"[PromptManager] Failed to load prompt {name}: {e}")
            return None
    
    def get(self, name: str, **kwargs) -> str:
        """
        Get a rendered prompt by name with variable substitution.
        
        Args:
            name: The prompt name (filename without .yaml extension)
            **kwargs: Template variables to substitute
            
        Returns:
            Rendered prompt string, or empty string if not found
        """
        # Load from cache or file
        if name not in self._cache:
            template = self._load_prompt(name)
            if template:
                self._cache[name] = template
            else:
                return ""
        
        template = self._cache[name]
        return template.render(**kwargs)
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get the raw PromptTemplate object for inspection."""
        if name not in self._cache:
            template = self._load_prompt(name)
            if template:
                self._cache[name] = template
        return self._cache.get(name)
    
    def reload(self, name: str = None) -> int:
        """
        Reload prompts from disk.
        
        Args:
            name: Specific prompt to reload, or None to reload all
            
        Returns:
            Number of prompts reloaded
        """
        if name:
            # Reload specific prompt
            if name in self._cache:
                del self._cache[name]
            template = self._load_prompt(name)
            if template:
                self._cache[name] = template
                logger.info(f"[PromptManager] Reloaded prompt: {name}")
                return 1
            return 0
        
        # Reload all prompts
        self._cache.clear()
        count = 0
        
        if self.prompts_dir.exists():
            for file_path in self.prompts_dir.glob("*.yaml"):
                prompt_name = file_path.stem
                template = self._load_prompt(prompt_name)
                if template:
                    self._cache[prompt_name] = template
                    count += 1
        
        logger.info(f"[PromptManager] Reloaded {count} prompts from {self.prompts_dir}")
        return count
    
    def list_prompts(self) -> list[dict]:
        """List all available prompts with metadata."""
        prompts = []
        
        if self.prompts_dir.exists():
            for file_path in self.prompts_dir.glob("*.yaml"):
                prompt_name = file_path.stem
                template = self.get_template(prompt_name)
                if template:
                    prompts.append({
                        "name": template.name,
                        "version": template.version,
                        "description": template.description,
                        "variables": template.variables
                    })
        
        return prompts


# Convenience function for quick access
def get_prompt(name: str, **kwargs) -> str:
    """Convenience function to get a rendered prompt."""
    return PromptManager.get_instance().get(name, **kwargs)


# Singleton instance for import
prompts = PromptManager.get_instance()
