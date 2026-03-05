"""
AutoGen-based Planner Agent for workflow orchestration with HITL.
"""
import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from opentelemetry import trace
from traceloop.sdk.decorators import workflow, task
try:
    from nemoguardrails import LLMRails, RailsConfig
    GUARDRAILS_AVAILABLE = True
except ImportError:
    LLMRails = None
    RailsConfig = None
    GUARDRAILS_AVAILABLE = False
from agents.executor import ExecutorAgent
from config import config
import logging
import asyncio
import json
import os
import datetime
from core.pii_redactor import redactor
from core.prompt_manager import prompts
import yaml
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_agent_config(agent_id: str) -> dict:
    """
    Load agent configuration from domains/<agent_id>/config.yaml.
    Returns dict with name, description, pills, tools, owned_mcps etc.
    """
    config_path = Path(__file__).parent / "domains" / agent_id / "config.yaml"
    if not config_path.exists():
        logger.warning(f"[AgentConfig] Config not found for {agent_id}: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"[AgentConfig] Failed to load config for {agent_id}: {e}")
        return {}


def get_agent_pills(agent_id: str, with_icons: bool = True) -> list[dict]:
    """
    Get pills for an agent from its config.yaml.
    Adds emoji icons if with_icons is True.
    """
    config = load_agent_config(agent_id)
    pills = config.get("pills", [])
    
    if not with_icons:
        return pills
    
    # Add icons based on pill action/value patterns
    icon_map = {
        "time": "⏰", "log": "📝", "pto": "🏖️", "policy": "📚", "payroll": "💰",
        "ticket": "🎫", "incident": "🆕", "approval": "✅", "search": "🔍", "issue": "🎫",
        "client": "🔍", "opportunity": "🎯", "pipeline": "📊", "meeting": "📅", "ingestion": "📥",
        "onboard": "🆕", "checklist": "📋", "setup": "⏰", "billing": "💳",
    }
    
    enhanced_pills = []
    for pill in pills:
        label = pill.get("label", "")
        value = pill.get("value", "").lower()
        
        # Find matching icon
        icon = ""
        for keyword, emoji in icon_map.items():
            if keyword in value or keyword in label.lower():
                icon = emoji
                break
        
        enhanced_pills.append({
            "label": f"{icon} {label}".strip() if icon else label,
            "action": pill.get("action", "ask"),
            "value": pill.get("value", "")
        })
    
    return enhanced_pills


def get_ui_template(tool_name: str, active_area: str = None) -> dict | None:
    """
    Get UI template for a tool from the active area's config.
    Returns None if no template is defined.
    """
    # Map area names to agent IDs
    area_to_agent = {
        "it_support": "it_support",
        "servicenow": "it_support",
        "hr": "hr",
        "workday": "hr",
        "sales": "sales",
        "d365": "sales",
        "onboarding": "onboarding",
        "pricing_assistant": "pricing_assistant",
    }
    
    # Determine which agent config to check
    agent_id = area_to_agent.get(active_area) if active_area else None
    
    if agent_id:
        # Check active agent's config first
        config = load_agent_config(agent_id)
        templates = config.get("ui_templates", {})
        if tool_name in templates:
            return templates[tool_name]
    
    # Fallback: check all agents for template
    for aid in ["it_support", "hr", "sales", "onboarding", "pricing_assistant"]:
        config = load_agent_config(aid)
        templates = config.get("ui_templates", {})
        if tool_name in templates:
            return templates[tool_name]
    
    return None


def apply_ui_template(template: dict, data: Any) -> dict:
    """
    Apply a UI template to tool output data.
    Returns a manifest dict ready for frontend rendering.
    """
    template_type = template.get("type", "table")
    title = template.get("title", "Results")
    
    if template_type == "table":
        # For tables, filter columns if specified
        columns = template.get("columns", [])
        if columns and isinstance(data, list):
            # Map column keys to labels
            column_labels = {c["key"]: c["label"] for c in columns}
            filtered_keys = [c["key"] for c in columns]
            
            return {
                "componentType": "table",
                "title": title,
                "columns": columns,
                "payload": data,
                "row_actions": template.get("row_actions", [])
            }
    
    elif template_type == "card_list":
        return {
            "componentType": "card_list",
            "title": title,
            "fields": template.get("fields", []),
            "payload": data,
            "primary_action": template.get("primary_action")
        }
    
    elif template_type == "success_card":
        return {
            "componentType": "success_card",
            "title": title,
            "fields": template.get("fields", []),
            "payload": data if isinstance(data, dict) else {}
        }
    
    elif template_type == "knowledge_card":
        return {
            "componentType": "knowledge_card",
            "title": title,
            "fields": template.get("fields", []),
            "payload": data
        }
    
    elif template_type == "markdown":
        # For markdown type, the data is already formatted text - just wrap it
        return {
            "componentType": "markdown",
            "title": title,
            "payload": str(data) if data else ""
        }
    
    # Fallback to generic table
    return {
        "componentType": "table",
        "payload": data if isinstance(data, list) else [data]
    }


class PlannerAgent:
    """
    Planner agent for orchestrating workflows with HITL confirmation.
    Uses AutoGen 0.7.x agents to process requests and call tools.
    """
    # Class-level cache for static CRM metadata
    _d365_metadata_cache: str | None = None
    _d365_metadata_last_fetched: datetime.datetime | None = None
    
    def __init__(self, executor: ExecutorAgent):
        self.executor = executor
        self.pending_confirmation: dict | None = None
        self.pending_plan: dict | None = None
        self.auth_token: str | None = None
        self._user_id: str | None = None
        self.auth_flow: str = "CLIENT_CREDENTIALS"
        self.active_d365_env: dict | None = None # { "url": "...", "tenant": "..." }
        self.active_area: str | None = None # e.g., "knowledge_hub", "d365"
        
        # NEW: Orchestrator for modular agent architecture
        self.orchestrator = None
        self._user_roles: list[str] = []
        try:
            from agents.orchestrator import Orchestrator
            self.orchestrator = Orchestrator()
            logger.info("[Planner] Orchestrator initialized for modular agents")
        except ImportError as e:
            logger.warning(f"[Planner] Orchestrator not available: {e}")
        
        # Initialize HTTP Client with SSL verification disabled for troubleshooting
        self.http_client = httpx.AsyncClient(verify=False)
        self.model_client = None
        self.assistant = None
        self._active_model = None
        
        # Default to the first available model
        self.rails = None
        self.switch_model()
        
        # Log active model on startup
        if self._active_model:
            logger.info(f"[Planner] 🤖 Active Model: {self._active_model.name} ({self._active_model.provider}) - {self._active_model.model_name}")

    def switch_model(self, model_id: str = None):
        """Switch the active LLM model."""
        model_def = config.get_model(model_id)
        if not model_def:
            print(f"[Planner] Model {model_id} not found, using default.")
            return

        print(f"[Planner] Switching to model: {model_def.name} ({model_def.provider})")
        self._active_model = model_def
        
        if model_def.provider == "local":
            # Local LLM (LM Studio, Ollama)
            self.model_client = OpenAIChatCompletionClient(
                model=model_def.model_name,
                api_key="not-needed",
                base_url=model_def.base_url,
                http_client=self.http_client,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "family": "gpt-4o",
                }
            )
        elif model_def.provider == "openai":
            # Regular OpenAI API
            self.model_client = OpenAIChatCompletionClient(
                model=model_def.model_name,
                api_key=model_def.api_key,
                base_url=model_def.base_url,
                http_client=self.http_client,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "family": "gpt-4o",
                }
            )
        else:
            # Azure OpenAI
            self.model_client = AzureOpenAIChatCompletionClient(
                azure_endpoint=model_def.base_url,
                api_key=model_def.api_key,
                api_version=model_def.api_version,
                model=model_def.model_name,
                http_client=self.http_client,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": "gpt-4o",
                }
            )
        
        # Reset lazy components so they re-initialize with new model client if needed
        self.rails = None
        self.assistant = None

    async def _ensure_rails(self):
        """Lazy initialization of NeMo Guardrails."""
        if self.rails:
            return self.rails
        
        # Skip if nemoguardrails is not installed
        if not GUARDRAILS_AVAILABLE:
            return None
        
        try:
            model_def = self._active_model
            if model_def and model_def.api_key:
                os.environ["OPENAI_API_KEY"] = model_def.api_key
                
            # Use absolute path for guardrails config to be resilient to CWD
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "core", "guardrails")
            
            if not os.path.exists(config_path):
                # Fallback to relative if for some reason absolute fails
                config_path = "iis/core/guardrails"
                
            rails_config = RailsConfig.from_path(config_path)
            self.rails = LLMRails(rails_config)
            print(f"[Planner] Guardrails lazy-initialized from {config_path}")
        except Exception as e:
            print(f"[Planner] Guardrails lazy-init failed: {e}")
            import traceback
            traceback.print_exc()
            self.rails = None
        return self.rails

    async def _ensure_assistant(self):
        """Lazy initialization of the AssistantAgent."""
        if self.assistant:
            return self.assistant
        
        persona_prefix = ""
        if hasattr(self, "user_name") and self.user_name:
            persona_name = "Executive Administrator" if "APP_ROLE_ADMIN" in self.user_roles else "Business User"
            persona_prefix = f"You are acting as {persona_name} ({self.user_name}).\n"
            if persona_name == "Business User":
                persona_prefix += "You have read-only access to business data.\n"
        
        # Load system persona from configurable prompt file
        system_message = prompts.get("system_persona", persona_prefix=persona_prefix)
        
        # Use area-filtered tools instead of all tools
        filtered_tools = self._get_area_tools()
        
        self.assistant = AssistantAgent(
            name="planner_assistant",
            model_client=self.model_client,
            system_message=system_message,
            tools=filtered_tools,
        )

        # Restore state if we have it
        if hasattr(self, "_pending_assistant_state") and self._pending_assistant_state:
            await self.assistant.load_state(self._pending_assistant_state)
            self._pending_assistant_state = None

        print(f"[Planner] Assistant agent lazy-initialized with {len(filtered_tools)} tools for area: {self.active_area or 'general'}")
        return self.assistant

    def _get_area_tools(self) -> list:
        """
        Filter tools based on active_area to prevent wrong tool selection.
        Each area gets only its relevant tools + shared tools (kb_*).
        """
        all_tools = self.executor.get_tools()
        
        if not self.active_area:
            # No active area - return all tools
            return all_tools
        
        # Define tool prefixes allowed for each area
        area_tool_prefixes = {
            "it_support": ["snow_", "kb_"],  # ServiceNow + Knowledge Hub
            "servicenow": ["snow_", "kb_"],
            "hr": ["wd_", "kb_"],  # Workday + Knowledge Hub
            "workday": ["wd_", "kb_"],
            "sales": ["d365_", "kb_"],  # Dynamics 365 + Knowledge Hub
            "d365": ["d365_", "kb_"],
            "onboarding": ["d365_", "wd_", "kb_"],  # CRM + Workday + KB
            "m365": ["graph_", "kb_"],  # Microsoft Graph + KB
            "knowledge_hub": ["kb_"],  # Only Knowledge Hub
            "pricing_assistant": ["pricing_", "d365_", "kb_"],  # Pricing + CRM + KB
        }
        
        allowed_prefixes = area_tool_prefixes.get(self.active_area)
        if not allowed_prefixes:
            # Unknown area - return all tools
            return all_tools
        
        # Filter tools by prefix
        filtered = [
            tool for tool in all_tools
            if any(tool.name.startswith(prefix) for prefix in allowed_prefixes)
        ]
        logger.info(f"[Planner] Filtered tools for '{self.active_area}': {[t.name for t in filtered]}")
        return filtered

    def set_persona(self, name: str, roles: list[str]):
        """Set the persona name and roles."""
        self.persona_name = name
        self._user_roles = roles
    
    def set_session_id(self, session_id: str):
        """Set the session ID for state persistence."""
        self._session_id = session_id
    
    async def save_state(self) -> dict:
        """Serialize relevant state for database persistence."""
        domain_state = getattr(self, "domain_agent_state", {})
        wizard_state_preview = domain_state.get("wizard_state", {})
        logger.info(f"[Planner] save_state: active_area='{self.active_area}', domain_agent_state wizard_state.current_phase='{wizard_state_preview.get('current_phase')}', collected_fields keys={list(wizard_state_preview.get('collected_fields', {}).keys())}")
        
        state = {
            "pending_confirmation": self.pending_confirmation,
            "pending_plan": self.pending_plan,
            "assistant_state": await self.assistant.save_state() if self.assistant else None,
            "user_name": getattr(self, "user_name", None),
            "user_roles": getattr(self, "user_roles", []),
            "auth_token": self.auth_token,
            "user_id": getattr(self, "_user_id", None),
            "user_email": getattr(self, "_user_email", None),
            "active_d365_env": self.active_d365_env,
            "active_area": self.active_area,
            "domain_agent_state": domain_state,  # Store domain agent state
        }
        
        return state

    async def load_state(self, state: dict):
        """Restore state from database."""
        if not state:
            logger.info("[Planner] load_state: No state to load")
            return
        
        # Log what's being loaded
        domain_state = state.get("domain_agent_state", {})
        wizard_state_preview = domain_state.get("wizard_state", {})
        logger.info(f"[Planner] load_state: active_area='{state.get('active_area')}', domain_agent_state wizard_state.current_phase='{wizard_state_preview.get('current_phase')}', collected_fields keys={list(wizard_state_preview.get('collected_fields', {}).keys())}")
        
        self.pending_confirmation = state.get("pending_confirmation")
        self.pending_plan = state.get("pending_plan")
        self.user_name = state.get("user_name")
        self.user_roles = state.get("user_roles", [])
        self.auth_token = state.get("auth_token")
        self._user_id = state.get("user_id")
        self._user_email = state.get("user_email")
        self.active_d365_env = state.get("active_d365_env")
        self.active_area = state.get("active_area")
        self.domain_agent_state = domain_state  # Load domain agent state
        
        # Store assistant state for lazy initialization
        self._pending_assistant_state = state.get("assistant_state")
        
        # Restore assistant state if present
        if self._pending_assistant_state and self.assistant:
            await self.assistant.load_state(self._pending_assistant_state)

    @property
    def model_info(self) -> str:
        """Get human-readable model information from current client."""
        if self._active_model:
            hosting = "Cloud" if self._active_model.provider in ["azure", "openai"] else "Local"
            return f"{hosting} - {self._active_model.name}"
        return "Active Model"

    def _get_d365_client(self):
        """Helper to create a D365Client based on the active environment selection."""
        from integrations.d365.service import D365Client
        if self.active_d365_env:
            return D365Client(
                resource_url=self.active_d365_env.get("url"),
                tenant_id=self.active_d365_env.get("tenant")
            )
        return D365Client() # Defaults to .env config

    async def _get_d365_metadata(self) -> str:
        """Fetch CRM option sets and lookups for UI discovery with caching."""
        # 1. Check Cache (1 hour TTL)
        now = datetime.datetime.now()
        # Key cache by environment URL to avoid mixing metadata
        env_url = (self.active_d365_env or {}).get("url", "default")
        cache_key = f"_d365_metadata_{env_url}"
        
        if (hasattr(self.__class__, cache_key) and 
            self._d365_metadata_last_fetched and 
            (now - self._d365_metadata_last_fetched).total_seconds() < 3600):
            return getattr(self.__class__, cache_key)

        try:
            async with self._get_d365_client() as client:
                ops = await client.get_option_sets()
                # Simplify for LLM: Just Name -> [Options]
                metadata = {}
                for field, mapping in ops.items():
                    metadata[field] = list(mapping.values())
                
                lookups = await client.get_lookups()
                for field, items in lookups.items():
                    metadata[field] = [item["name"] for item in items]
                    
                import json
                setattr(self.__class__, cache_key, json.dumps(metadata))
                self.__class__._d365_metadata_last_fetched = now
                logger.info(f"[Planner] Cached D365 metadata for {env_url} with {len(metadata)} fields.")
                return getattr(self.__class__, cache_key)
        except Exception as e:
            logger.warning(f"Could not fetch D365 metadata for UI generator: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return "{}"

    async def set_auth_info(self, token: str, auth_flow: str = None, user_id: str = None, email: str = None, roles: list[str] = None):
        """Set authentication token and flow for backend requests."""
        self.auth_token = token
        if auth_flow:
            self.auth_flow = auth_flow
            
        # Priority: explicit email (for credentials) > user_id (likely GUID)
        if email:
            self._user_email = email
        if user_id:
            self._user_id = user_id
            # Heuristic: If user_id looks like an email and _user_email is not set, use it
            if "@" in user_id and not (getattr(self, "_user_email", None)):
                self._user_email = user_id

        # NEW: Store user roles for agent entitlement checks
        if roles:
            self._user_roles = roles
            logger.info(f"[Planner] User roles set: {roles}")
        
        # Sync orchestrator context
        if self.orchestrator:
            self.orchestrator.set_user_context(
                roles=self._user_roles,
                user_id=user_id,
                email=getattr(self, "_user_email", None)
            )

        await self._sync_context()

    async def _sync_context(self):
        """Sync internal state to thread-local context variables."""
        from core.context import auth_token_ctx, auth_user_ctx
        if self.auth_token:
            auth_token_ctx.set(self.auth_token)
        
        # Use email for context if available, as integrations (ServiceNow) key off it
        context_user = getattr(self, "_user_email", None) or getattr(self, "_user_id", None)
        logger.debug(f"[Planner] Syncing context: user_email={getattr(self, '_user_email', None)}, user_id={getattr(self, '_user_id', None)} -> context_user={context_user}")
        if context_user:
            auth_user_ctx.set(context_user)
        
        # Update executor's token as well
        if self.executor and self.auth_token:
            self.executor.set_auth_token(self.auth_token)

    @task(name="intent_detection")
    async def _get_intent(self, message: str) -> dict:
        """Use LLM to detect user intent and extract parameters."""
        # Load intent detection prompt from configurable YAML file
        prompt = prompts.get("intent_detection", message=message)
        
        try:
            # Create a simple message for the model client
            from autogen_core.models import SystemMessage, UserMessage
            response = await self.model_client.create(
                messages=[
                    SystemMessage(content="You are an intent classifier that returns JSON."),
                    UserMessage(content=prompt, source="user")
                ]
            )
            content = response.content
            print(f"[Planner] Raw Intent Response: {content}")
            
            # Clean up JSON if model adds markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            return json.loads(content)
        except Exception as e:
            print(f"[Planner] Intent detection failed: {e}")
            import traceback
            traceback.print_exc()
            return {"intent": "general_query", "parameters": {}}

    async def process_message(
        self,
        user_message: str,
        values: dict = None,
        on_step: callable = None,
    ) -> dict:
        """Process a user message using AutoGen agents."""
        await self._sync_context()
        # NEW: Direct deterministic trigger for discovery (Greetings/Help)
        clean_msg = str(user_message).lower().strip().replace("!", "").replace(".", "")
        is_greeting = clean_msg in ["hi", "hello", "hey", "start", "menu", "discovery", "welcome"]
        is_help = any(kw in clean_msg for kw in ["help", "/help", "what can you do"])
        
        if (is_greeting and len(clean_msg) <= 12) or (is_help and len(clean_msg) <= 20):
            if on_step:
                await on_step("Opening Area selection menu...")
            
            # Build personalized greeting
            user_greeting = f"Hello **{self.user_name}**! " if hasattr(self, 'user_name') and self.user_name else "Hello! "
            
            # Build pills based on user's entitled agents
            base_pills = [
                { "label": "📚 Knowledge Hub", "action": "select_area", "value": "knowledge_hub" },
                { "label": "🛠️ IT Support", "action": "select_area", "value": "it_support" },
                { "label": "👥 HR", "action": "select_area", "value": "hr" },
            ]
            
            # Add specialized agent pills if user is entitled
            if self.orchestrator:
                from agents.entitlements import get_available_agents, AGENT_METADATA
                user_roles = getattr(self, 'user_roles', [])
                logger.info(f"[Planner] Building pills - user_roles: {user_roles}")
                available = get_available_agents(user_roles)
                logger.info(f"[Planner] Available specialized agents: {available}")
                specialized_ids = ['sales', 'onboarding', 'pricing_assistant']
                for agent_id in specialized_ids:
                    logger.info(f"[Planner] Checking {agent_id} in available: {agent_id in available}")
                    if agent_id in available:
                        meta = AGENT_METADATA.get(agent_id, {})
                        pill = {
                            "label": f"{meta.get('icon', '🤖')} {meta.get('name', agent_id).replace(' Agent', '')}",
                            "action": "select_area",
                            "value": agent_id
                        }
                        logger.info(f"[Planner] Adding pill: {pill}")
                        base_pills.append(pill)
            
            logger.info(f"[Planner] Final pills payload: {[p['label'] for p in base_pills]}")
            return {
                "type": "assistant_manifest",
                "content": f"{user_greeting}How can I help you today?",
                "manifest": {
                    "componentType": "pills",
                    "payload": base_pills
                }
            }

        span = trace.get_current_span()
        if span:
            # Redact PII before setting attributes
            redacted_msg, msg_pii_count = redactor.redact(user_message)
            span.set_attribute("app.user_message", redacted_msg)
            
            total_pii_count = msg_pii_count
            
            if self._active_model:
                span.set_attribute("gen_ai.request.model", self._active_model.model_name)
                
            if hasattr(self, "user_name") and self.user_name:
                redacted_name, name_pii_count = redactor.redact(self.user_name)
                span.set_attribute("app.user_name", redacted_name)
                total_pii_count += name_pii_count
            
            if total_pii_count > 0:
                span.set_attribute("pii.redaction_count", total_pii_count)
                span.set_attribute("pii.protected", True)

        async def emit(content, stage: str = None, tool: str = None, status: str = "complete", details: dict = None):
            """Emit thought/reasoning step. Supports both legacy string and structured dict."""
            if on_step:
                if isinstance(content, dict):
                    # Already structured - pass through
                    await on_step(content)
                elif stage:
                    # Create structured reasoning event
                    await on_step({
                        "type": "reasoning",
                        "stage": stage,
                        "tool": tool,
                        "status": status,
                        "message": content,
                        "details": details or {}
                    })
                else:
                    # Legacy string format - wrap for backwards compatibility
                    await on_step(content)

        # Check if this is a confirmation response
        if self.pending_plan:
            await emit("Resuming planned workflow...")
            return await self._handle_plan_confirmation(user_message, values)
        
        if self.pending_confirmation:
            await emit("Processing confirmation...")
            return await self._handle_confirmation(user_message, values)
        
        # --- Phase 1: Security & Intent (Parallelized) ---
        await emit("Analyzing request & security policies", stage="security_check", status="in_progress")
        
        # Deterministic Intent Fast-Path (Skip LLM if possible)
        # ONLY trigger KB fast-path if NOT already in a tool-based area
        fast_intent = None
        tool_based_areas = ["it_support", "servicenow", "hr", "workday", "sales", "d365", "onboarding", "m365"]
        
        if self.active_area not in tool_based_areas:
            # Only trigger KB search for policy/procedure questions when no specific area selected
            kb_keywords = ["policy", "travel", "expense", "holiday", "benefits", "dress code", "dress", "handbook", "procedure", "guideline", "firm", "knowledge hub"]
            if any(kw in user_message.lower() for kw in kb_keywords):
                fast_intent = {"intent": "knowledge_base_search", "parameters": {}}
                logger.info(f"[Planner] Fast-intent detected: knowledge_base_search (no active tool area)")

        async def run_rails():
            if self.rails or (not is_greeting and not is_help):
                rails = await self._ensure_rails()
                if rails:
                    try:
                        resp = await rails.generate_async(prompt=user_message)
                        return resp if (resp and "GUARDRAIL_BLOCKED" in resp) else None
                    except Exception as e:
                        logger.error(f"[FIREWALL] NeMo error: {e}")
            return None

        async def run_custom_firewall():
            if len(user_message) > 25:
                # Load scope classifier from configurable YAML file
                is_in_scope_prompt = prompts.get("scope_classifier", message=user_message)
                try:
                    from autogen_core.models import UserMessage
                    check_res = await self.model_client.create(messages=[UserMessage(content=is_in_scope_prompt, source="user")])
                    if check_res and "UNRELATED" in str(check_res.content).upper():
                        return "I am a specialized AI assistant for Enterprise Systems. That request is outside my domain."
                except Exception as ex:
                    logger.error(f"[FIREWALL] Custom check failed: {ex}")
            return None

        async def run_intent_detection():
            if fast_intent: return fast_intent
            intent_query = user_message
            if self.active_area:
                intent_query = f"[Context: {self.active_area}] {user_message}"
            return await self._get_intent(intent_query)

        # Execute parallel tasks - skip firewall checks if fast_intent detected (trusted KB query)
        if fast_intent:
            # Fast path: KB keywords detected, skip expensive firewall checks
            rails_block, custom_block, intent_data = None, None, fast_intent
            logger.info("[Planner] Fast-intent bypassing firewall checks for KB query")
        else:
            tasks = [run_rails(), run_custom_firewall(), run_intent_detection()]
            rails_block, custom_block, intent_data = await asyncio.gather(*tasks)
        
        block_response = rails_block or custom_block

        # If blocked, return refusal
        if block_response:
            span = trace.get_current_span()
            if span:
                span.set_attribute("security.firewall_blocked", True)
            await emit("Request blocked by security firewall.")
            return {
                "type": "assistant_manifest",
                "content": block_response,
                "manifest": {"componentType": "info", "payload": {"status": "error", "message": "Policy Refusal."}}
            }

        await emit(f"Intent detected: {intent_data.get('intent', 'general query')}", stage="intent_detection", status="complete")
        
        if intent_data.get("intent") == "knowledge_base_search" or (self.active_area == "knowledge_hub" and "search" in user_message.lower()):
            await emit("Searching Knowledge Hub...")
            user_message = f"Use kb_search to answer this: {user_message}"
        
        if intent_data.get("intent") == "update_client_stage":
            params = intent_data.get("parameters", {})
            await emit(f"Initiating stage update for {params.get('client_name')}...")
            return await self._handle_stage_update_hitl(user_message, client_name=params.get("client_name"), new_stage=params.get("new_stage"))
        
        # Handle HR Time Entry intent - route to HR agent with time entry tools
        if intent_data.get("intent") == "hr_time_entry":
            params = intent_data.get("parameters", {})
            action = params.get("action", "log")
            self.active_area = "hr"  # Force HR area
            if action == "view":
                await emit("Fetching your timesheet...", stage="tool_execution", tool="wd_get_my_timesheet", status="in_progress")
                user_message = f"Use wd_get_my_timesheet to show the user's timesheet for this week. Original request: {user_message}"
            else:
                await emit("Preparing time entry...", stage="tool_execution", tool="wd_add_time_entry", status="in_progress")
                hours = params.get("hours", "")
                project_hint = params.get("project_hint", "")
                user_message = f"Use wd_add_time_entry to log time. Hours: {hours}. Project hint: {project_hint}. Original request: {user_message}"
        
        # DEBUG: Log active_area before delegation check
        logger.info(f"[Planner] DEBUG - active_area: '{self.active_area}', orchestrator exists: {self.orchestrator is not None}")
        
        # --- DOMAIN AGENT DELEGATION ---
        # Route to orchestrator for specialized domain agents
        domain_agents = ["sales", "onboarding", "pricing_assistant"]
        if self.active_area in domain_agents and self.orchestrator:
            await emit(f"Routing to {self.active_area} agent", stage="orchestration", status="in_progress")
            logger.info(f"[Planner] Delegating to orchestrator for {self.active_area}")
            
            # Set user context in orchestrator
            self.orchestrator.set_user_context(
                roles=self._user_roles,
                user_id=self._user_id,
                email=getattr(self, '_user_email', None)
            )
            
            # Get session_id
            session_id = getattr(self, '_session_id', 'unknown')
            logger.info(f"[Planner] Setting orchestrator context: roles={self._user_roles}, user_id={self._user_id}")
            
            # Get domain agent state from planner's state
            if not hasattr(self, 'domain_agent_state'):
                self.domain_agent_state = {}
            
            # Process through orchestrator with domain state in context
            orchestrator_response = await self.orchestrator.process_message(
                message=user_message, # Changed from 'query' to 'user_message' to match existing variable
                active_area=self.active_area,
                session_id=session_id,
                on_step=on_step,
                context=self.domain_agent_state  # Pass domain agent state
            )
            
            # Extract result and updated context
            if isinstance(orchestrator_response, dict) and "result" in orchestrator_response:
                result = orchestrator_response["result"]
                updated_context = orchestrator_response.get("context", {})
                
                # Save wizard_state back to domain_agent_state if it was updated
                if "wizard_state" in updated_context:
                    self.domain_agent_state["wizard_state"] = updated_context["wizard_state"]
                    logger.info(f"[Planner] Saved wizard_state to domain_agent_state")
            else:
                # Backward compatibility: orchestrator returned result directly
                result = orchestrator_response
            
            # Check if orchestrator returned a fallback signal (agent not implemented)
            if result.get("fallback"):
                logger.info(f"[Planner] Orchestrator fallback - using legacy flow for {self.active_area}")
                # Continue to legacy AutoGen flow below
            else:
                # Orchestrator handled it - return the result
                logger.info(f"[Planner] Orchestrator handled {self.active_area} request")
                return result
        
        # For simple lookups or general queries, use the AutoGen agent
        try:
            assistant = await self._ensure_assistant()
            await emit("Orchestrating agent task", stage="orchestration", status="in_progress")
            
            # Inject stateful context into the agent turn
            agent_task = user_message
            if self.active_area:
                # Map areas to their preferred tools for stronger LLM hints
                area_tool_hints = {
                    "it_support": "Use ServiceNow tools (snow_search_incidents, snow_create_incident, snow_list_approvals). Do NOT use kb_search for ticket queries.",
                    "servicenow": "Use ServiceNow tools (snow_search_incidents, snow_create_incident, snow_list_approvals).",
                    "hr": "Use Time Entry tools (wd_add_time_entry, wd_get_my_timesheet) for time logging. Use kb_search only for policy questions.",
                    "workday": "Use Workday tools (wd_add_time_entry, wd_get_my_timesheet, wd_get_customer_accounts).",
                    "sales": "Use Dynamics 365 tools (d365_search_accounts, d365_create_opportunity).",
                    "d365": "Use Dynamics 365 tools (d365_search_accounts, d365_create_account, d365_smart_ingestion).",
                    "onboarding": "Use D365 tools for CRM and Workday tools for time/billing setup.",
                    "m365": "Use Microsoft Graph tools (graph_list_events, graph_list_messages).",
                    "knowledge_hub": "Use Knowledge Hub tools (kb_search, kb_list_domains).",
                    "pricing_assistant": "Guide user through pricing wizard. Use D365 tools for CRM context.",
                }
                
                tool_hint = area_tool_hints.get(self.active_area, "")
                agent_task = f"[Active Area: {self.active_area}] [Tool Hint: {tool_hint}] {user_message}"
                
                # Emit area-specific progress with tool execution stage
                area_tool_mapping = {
                    "servicenow": ("snow_search_incidents", "Querying ServiceNow API"),
                    "it_support": ("snow_search_incidents", "Querying ServiceNow API"),
                    "d365": ("d365_search_accounts", "Accessing Dynamics 365 CRM"),
                    "sales": ("d365_search_accounts", "Accessing Dynamics 365 CRM"),
                    "workday": ("wd_add_time_entry", "Fetching Workday data"),
                    "hr": ("wd_add_time_entry", "Processing time entry"),
                    "m365": ("graph_list_events", "Connecting to Microsoft 365"),
                    "knowledge_hub": ("kb_search", "Searching Knowledge Hub"),
                    "onboarding": ("d365_create_account", "Coordinating D365 + Workday"),
                    "pricing_assistant": ("pricing_wizard", "Initializing Pricing Wizard"),
                }
                if self.active_area in area_tool_mapping:
                    tool_name, label = area_tool_mapping[self.active_area]
                    await emit(label, stage="tool_execution", tool=tool_name, status="in_progress")
                
            print(f"[Planner] Running agent task: {agent_task}")
            result = await assistant.run(task=agent_task)
            await emit("Processing results", stage="data_processing", status="in_progress")
            
            # --- BLAZING FAST UI ENGINE (Deterministic & Inline) ---
            last_message = result.messages[-1].content if result.messages else ""
            
            # DEBUG: Log all messages to understand structure
            logger.info(f"[Planner] UI Engine - Active area: {self.active_area}")
            logger.info(f"[Planner] UI Engine - Total messages: {len(result.messages)}")
            for i, msg in enumerate(result.messages):
                src = getattr(msg, "source", "unknown")
                content_preview = str(msg.content)[:150].replace("\n", " ")
                logger.info(f"[Planner] Message[{i}] source='{src}' content='{content_preview}...'")
            
            # 0. Config-Driven Template Detection (NEW - Highest Priority)
            # Check if any tool call has a UI template defined in agent config
            for msg in reversed(result.messages):
                msg_content = str(msg.content)
                source = getattr(msg, "source", "unknown")
                
                # Skip user messages - we want tool outputs (which come from planner_assistant)
                if source == "user":
                    continue
                
                # Debug: log the source to understand message structure
                logger.debug(f"[Planner] Template check - source: {source}, content preview: {msg_content[:100]}...")
                
                # Try to identify the tool name from the content
                # Tool outputs contain FunctionExecutionResult or JSON data with tool names
                tool_name = None
                
                # Check if any known tool names appear in the content
                known_tools = ["snow_search_incidents", "snow_create_incident", "snow_list_approvals", 
                              "wd_get_time_entries", "d365_search_accounts", "kb_search", "graph_list_events"]
                for kt in known_tools:
                    if kt in msg_content.lower() or kt in source.lower():
                        tool_name = kt
                        logger.info(f"[Planner] Detected tool from content: {tool_name}")
                        break
                
                if not tool_name:
                    continue  # No known tool found in this message
                
                # Check if we have a template for this tool
                template = get_ui_template(tool_name, self.active_area)
                if template:
                    template_type = template.get("type", "")
                    
                    import re
                    # Extract raw text from AutoGen FunctionExecutionResult wrappers
                    clean_content = msg_content
                    if "FunctionExecutionResult(" in clean_content:
                        match = re.search(r"FunctionExecutionResult\(content=(.*?),\s*name=", clean_content, re.DOTALL)
                        if match:
                            inner = match.group(1).strip()
                            if (inner.startswith("'") and inner.endswith("'")) or (inner.startswith('"') and inner.endswith('"')):
                                inner = inner[1:-1]
                            if "TextContent(type=" in inner and "text=" in inner:
                                text_match = re.search(r"text=(?:'|\")(.*?)(?:'|\"), annotations=", inner, re.DOTALL)
                                if text_match:
                                    inner = text_match.group(1)
                            clean_content = inner.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')

                    # For markdown templates, use raw text content directly
                    if template_type == "markdown":
                        await emit("Generating UI (Markdown Template)", stage="ui_generation", tool=tool_name, status="complete")
                        logger.info(f"[Planner] Config-driven markdown template applied for {tool_name}")
                        
                        manifest = apply_ui_template(template, clean_content)
                        return {
                            "type": "assistant_manifest",
                            "content": last_message.split("MANIFEST:")[0].strip() if "MANIFEST:" in last_message else last_message,
                            "manifest": manifest
                        }
                    
                    # For JSON-based templates, parse the content
                    try:
                        # Extract JSON from AutoGen TextContent wrapper format
                        # Content can look like: "([TextContent(type='text', text='[{...}]', ...)]"
                        # or: "[FunctionExecutionResult(content='...')"
                        extracted_json = None
                        
                        import re
                        
                        # Strategy 1: Find JSON array between [{ and }] with greedy matching
                        # Look for the actual JSON data pattern
                        if '[{' in msg_content:
                            # Find the start of JSON array
                            start_idx = msg_content.find('[{"')
                            if start_idx == -1:
                                start_idx = msg_content.find("[{'")
                            
                            if start_idx != -1:
                                # Find matching end - look for }] followed by non-JSON char
                                depth = 0
                                end_idx = start_idx
                                for i, c in enumerate(msg_content[start_idx:]):
                                    if c == '[':
                                        depth += 1
                                    elif c == ']':
                                        depth -= 1
                                        if depth == 0:
                                            end_idx = start_idx + i + 1
                                            break
                                
                                if end_idx > start_idx:
                                    extracted_json = msg_content[start_idx:end_idx]
                                    logger.info(f"[Planner] Extracted JSON array from content (len={len(extracted_json)})")
                        
                        # Strategy 2: Try direct JSON if content starts with [
                        if not extracted_json and msg_content.strip().startswith('[{'):
                            extracted_json = msg_content.strip()
                        
                        if extracted_json:
                            # Clean up escaped quotes - handle both \" and \' patterns
                            clean_content = extracted_json
                            clean_content = clean_content.replace('\\"', '"')
                            clean_content = clean_content.replace("\\'", "'")
                            # Replace single quotes with double quotes for JSON compatibility
                            # But be careful not to break already-valid JSON
                            if "'" in clean_content and '"' not in clean_content:
                                clean_content = clean_content.replace("'", '"')
                            
                            logger.debug(f"[Planner] Attempting to parse: {clean_content[:100]}...")
                            data = json.loads(clean_content)
                            
                            await emit("Generating UI (Config Template)", stage="ui_generation", tool=tool_name, status="complete")
                            logger.info(f"[Planner] Config-driven UI template applied for {tool_name}")
                            
                            manifest = apply_ui_template(template, data)
                            
                            # Generate clean content message from template
                            template_title = template.get("title", "Results")
                            if isinstance(data, list):
                                content_msg = f"**{template_title}** - Found {len(data)} record(s)."
                            else:
                                content_msg = f"**{template_title}**"
                            
                            return {
                                "type": "assistant_manifest",
                                "content": content_msg,
                                "manifest": manifest
                            }
                    except json.JSONDecodeError as je:
                        logger.warning(f"[Planner] JSON decode failed for {tool_name}: {je}")
                    except Exception as te:
                        logger.warning(f"[Planner] Template application failed for {tool_name}: {te}")
            
            # 1. Fallback: Deterministic Table Detection (Zero-LLM)
            # If the last tool output was a list of objects, we automatically table it
            for msg in reversed(result.messages):
                msg_content = str(msg.content)
                source = getattr(msg, "source", "unknown")
                
                # We only care about tool results (not-assistant messages) that look like lists
                if source != "planner_assistant" and "[" in msg_content:
                    try:
                        # Pre-process for common single-quote JSON-like output from Python tools
                        clean_content = msg_content.replace("'", '"')
                        data = json.loads(clean_content)
                        
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            await emit("Generating UI (Auto-Detected Table)", stage="ui_generation", status="complete")
                            logger.info(f"[Planner] Deterministic UI Table triggered for {source}")
                            return {
                                "type": "assistant_manifest",
                                "content": last_message.split("MANIFEST:")[0].strip(),
                                "manifest": {"componentType": "table", "payload": data}
                            }
                    except Exception as je:
                        logger.debug(f"[Planner] Deterministic parse skip for {source}: {je}")

            # 2. Inline Manifest Detection (Skip Formatting Pass)
            if "MANIFEST:" in last_message:
                try:
                    parts = last_message.split("MANIFEST:")
                    main_content = parts[0].strip()
                    manifest_json = json.loads(parts[1].strip().replace("'", '"'))
                    await emit("Generating UI (Inline Manifest)", stage="ui_generation", status="complete")
                    logger.info(f"[Planner] Inline UI Manifest triggered.")
                    return {
                        "type": "assistant_manifest",
                        "content": main_content,
                        "manifest": manifest_json
                    }
                except Exception as me:
                    logger.debug(f"[Planner] Inline manifest parse failed: {me}")

            # 3. Fallback to formatting pass (if needed)
            await emit("Generating UI (LLM Formatting)", stage="ui_generation", status="in_progress")
            logger.info(f"[Planner] Falling back to LLM for UI manifest.")
            # Use the new Response Formatter pass to create a UI Manifest
            # We pass the original task and the message history to the formatter
            manifest_response = await self._format_response(user_message, result.messages)
            
            return {
                "type": "assistant_manifest",
                "content": manifest_response.get("content", "Task completed."),
                "manifest": manifest_response.get("manifest")
            }
        except Exception as e:
            print(f"[Planner] Agent execution error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "type": "error",
                "content": f"Error during agent execution: {str(e)}",
            }

    @task(name="response_formatting")
    async def _format_response(self, task: str, messages: list) -> dict:
        """
        Final pass to format the agent's output into a UI Manifest.
        """
        # Lazy/Conditional Fetching of CRM metadata for the generator
        # Strategy: Only fetch if D365 tools were actually called in this session
        d365_tools = ["d365_", "list_opportunities", "search_clients", "opportunity_customer_accounts"]
        needs_d365_metadata = any(kw in str(messages).lower() for kw in d365_tools)
        
        metadata_str = "{}"
        if needs_d365_metadata:
            logger.info("[Planner] Detected D365 tool usage. Fetching enterprise metadata...")
            metadata_str = await self._get_d365_metadata()

        # Prepare context
        history = []
        has_complex_data = False
        for msg in messages:
            source = getattr(msg, "source", "unknown")
            content = getattr(msg, "content", "")
            if content:
                history.append(f"[{source}]: {content}")
                # Heuristic for complex data (lists, JSON, etc.)
                if any(c in content for c in ['[', '{', 'Source:', '|', '\t']):
                    has_complex_data = True
        
        history_str = "\n".join(history)
        
        # FAST PATH: If no complex data and no tool calls, return simple markdown manifest
        if not has_complex_data and len(messages) <= 2:
            last_text = messages[-1].content if messages else "Task completed."
            return {
                "content": last_text,
                "manifest": {"componentType": "markdown", "payload": ""}
            }
        # Get ONLY relevant tool definitions
        tools = self.executor.get_tools()
        tool_defs = []
        for t in tools:
            # Filter: Is this tool relevant to the current task or history?
            if t.name in history_str or t.name in task.lower():
                args = []
                if hasattr(t, 'func') and hasattr(t.func, '__annotations__'):
                    args = list(t.func.__annotations__.keys())
                    if 'return' in args: args.remove('return')
                tool_defs.append(f"- {t.name}: expects keys {args}")
        
        valid_tools_str = "\n".join(tool_defs) if tool_defs else "No relevant tools used."
        
        # Load UI manifest generator prompt from configurable YAML file
        prompt = prompts.get(
            "ui_manifest_generator",
            task=task,
            history_str=history_str,
            valid_tools_str=valid_tools_str,
            metadata_str=metadata_str
        )
        
        from autogen_core.models import SystemMessage, UserMessage
        try:
            response = await self.model_client.create(
                messages=[
                    SystemMessage(content="You are a UI manifest generator that returns JSON."),
                    UserMessage(content=prompt, source="user")
                ]
            )
            
            content = response.content
            print(f"[Planner] Raw Manifest Response: {content}")
            
            # Clean up JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            return json.loads(content)
        except Exception as e:
            print(f"[Planner] Response formatting failed: {e}")
            return {
                "content": "Task completed. Check logs for details.",
                "manifest": {"componentType": "markdown", "payload": ""}
            }

    async def generate_title(self, user_message: str, assistant_response: str) -> str:
        """Generate a concise, human-readable title for the chat session."""
        # Load title generator prompt from configurable YAML file
        prompt = prompts.get("title_generator", user_message=user_message, assistant_response=assistant_response)
        
        from autogen_core.models import SystemMessage, UserMessage
        try:
            # We explicitly use the model client to generate a simple completion
            response = await self.model_client.create(
                messages=[
                    SystemMessage(content="You are a title generator. Return only the title text."),
                    UserMessage(content=prompt, source="user")
                ]
            )
            title = response.content.strip().replace('"', '')
            return title[:50] # Sanity limit
        except Exception as e:
            print(f"[Planner] Title generation failed: {e}")
            return "New Chat"

    async def _handle_stage_update_hitl(self, message: str, client_name: str = None, new_stage: str = None) -> dict:
        """
        Dynamically trigger the YAML plan using extracted parameters.
        """
        # Resolve client_id from name (simple normalization)
        client_id = client_name.lower().replace(" ", "-") if client_name else "acme-corp"
        new_stage = new_stage or "qualified"
        
        # Initiate the plan in the backend
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "X-OpsIQ-Auth-Flow": self.auth_flow
            } if self.auth_token else {}
            ssl_verify = getattr(config, 'SSL_VERIFY', True)
            async with httpx.AsyncClient(verify=ssl_verify) as client:
                res = await client.post(
                    f"{config.backend_url}/api/v1/plans/client_onboarding_stage_update/execute",
                    json={"client_id": client_id, "new_stage": new_stage},
                    headers=headers
                )
                res.raise_for_status()
                plan_res = res.json()
                
                if not plan_res.get("success", True):
                    return {"type": "error", "content": plan_res.get("error", "Plan execution failed.")}

                if plan_res.get("status") == "paused":
                    # Store plan state
                    self.pending_plan = {
                        "plan_id": plan_res["plan_id"],
                        "step_index": plan_res["step_index"],
                        "context": plan_res["context"],
                    }
                    
                    hitl = plan_res["confirmation_request"]
                    return {
                        "type": "confirmation_request",
                        "content": hitl["description"],
                        "confirmation_data": hitl["schema"],
                    }
                
                return {"type": "assistant_message", "content": plan_res.get("message", "Plan completed successfully.")}
        except Exception as e:
            return {"type": "error", "content": f"Failed to initiate plan: {str(e)}"}

    async def handle_form_response(self, action: str, values: dict, on_step: callable = None) -> dict:
        """Handle a direct form submission or navigation action."""
        await self._sync_context()
        print(f"[DEBUG] handle_form_response: action={action}, values={values}")
        
        # New: 'start_wizard' action to initiate domain agent wizards
        if action == "start_wizard":
            # Route to orchestrator for domain agents
            domain_agents = ["sales", "onboarding", "pricing_assistant"]
            if self.active_area in domain_agents and self.orchestrator:
                logger.info(f"[Planner] Starting wizard for {self.active_area} via orchestrator")
                
                # Set user context
                self.orchestrator.set_user_context(
                    roles=self._user_roles,
                    user_id=self._user_id,
                    email=getattr(self, 'user_email', None)
                )
                
                # Get session_id from context
                session_id = getattr(self, '_session_id', 'unknown')
                
                # Get domain agent state from planner's state
                if not hasattr(self, 'domain_agent_state'):
                    self.domain_agent_state = {}
                
                # Process through orchestrator with start_wizard message and domain state
                wizard_type = values.get("value", "wizard")
                orchestrator_response = await self.orchestrator.process_message(
                    message=f"start_wizard {wizard_type}",
                    active_area=self.active_area,
                    session_id=session_id,
                    on_step=on_step,
                    context=self.domain_agent_state  # Pass domain agent state for persistence
                )
                
                # Extract result and updated context (CRITICAL: save initial wizard_state)
                if isinstance(orchestrator_response, dict) and "result" in orchestrator_response:
                    result = orchestrator_response["result"]
                    updated_context = orchestrator_response.get("context", {})
                    
                    # Save wizard_state back to domain_agent_state if it was updated
                    if "wizard_state" in updated_context:
                        self.domain_agent_state["wizard_state"] = updated_context["wizard_state"]
                        logger.info(f"[Planner] Saved initial wizard_state to domain_agent_state: phase={updated_context['wizard_state'].get('current_phase')}")
                else:
                    # Backward compatibility: orchestrator returned result directly
                    result = orchestrator_response
                
                return result
            else:
                return {"type": "error", "content": f"No wizard available for area: {self.active_area}"}
        
        # Handle pricing wizard form submissions
        pricing_form_actions = [
            "submit_core_fields",
            "submit_tax_fields",
            "submit_aa_fields",
            "submit_managed_acct_fields",
            "submit_consulting_snow_fields",
            "submit_consulting_d365_fields"
        ]
        
        if action in pricing_form_actions:
            if self.active_area == "pricing_assistant" and self.orchestrator:
                logger.info(f"[Planner] Routing {action} to pricing_assistant agent")
                
                # Set user context in orchestrator
                self.orchestrator.set_user_context(
                    roles=self._user_roles,
                    user_id=self._user_id,
                    email=getattr(self, 'user_email', None)
                )
                
                # Get session_id
                session_id = getattr(self, '_session_id', 'unknown')
                
                # Get domain agent state from planner's state
                if not hasattr(self, 'domain_agent_state'):
                    self.domain_agent_state = {}
                
                # Process through orchestrator with form values and domain state in context
                orchestrator_response = await self.orchestrator.process_message(
                    message=action,
                    active_area=self.active_area,
                    session_id=session_id,
                    on_step=on_step,
                    context={
                        "values": values,
                        "action": action,
                        **self.domain_agent_state  # Spread domain agent state into context
                    }
                )
                
                # Extract result and updated context
                if isinstance(orchestrator_response, dict) and "result" in orchestrator_response:
                    result = orchestrator_response["result"]
                    updated_context = orchestrator_response.get("context", {})
                    
                    # Save wizard_state back to domain_agent_state if it was updated
                    if "wizard_state" in updated_context:
                        self.domain_agent_state["wizard_state"] = updated_context["wizard_state"]
                        logger.info(f"[Planner] Saved wizard_state to domain_agent_state")
                else:
                    # Backward compatibility: orchestrator returned result directly
                    result = orchestrator_response
                
                return result
            else:
                return {"type": "error", "content": "Form submission failed: pricing_assistant not active"}
        
        
        # New: 'ask' action to allow pills to trigger conversational queries
        if action == "ask":
            # Extract areaId if present (sent by frontend when clicking pills)
            area_id = values.get("areaId")
            if area_id:
                logger.info(f"[Planner] ask action: Setting active_area to '{area_id}' from areaId")
                self.active_area = area_id
                # Reset assistant so it reloads with area-filtered tools
                self.assistant = None
            
            query = values.get("value") or values.get("question")
            if not query:
                return {"type": "error", "content": "No query provided for 'ask' action."}
            if on_step:
                await on_step({"type": "reasoning", "stage": "intent_detection", "status": "in_progress", "message": f"Processing query: {query[:40]}..."})
            return await self.process_message(query, on_step=on_step)

        if action == "open_url":
            # Frontend handles this, but we acknowledge it if it leaks to backend
            return {"type": "system_message", "content": "Opening external link..."}

        if action == "select_d365_environment":
            env_url = values.get("url")
            env_tenant = values.get("tenant")
            if env_url:
                self.active_d365_env = {"url": env_url, "tenant": env_tenant}
                # Reset metadata cache key for next lookup
                if on_step:
                    await on_step(f"Connected to D365 environment: {env_url}")
                return {"type": "assistant_message", "content": f"I've switched your active Dynamics 365 environment to: **{env_url}**."}
            return {"type": "error", "content": "No environment URL provided."}

        if action == "select_area":
            area_value = values.get("value")
            self.active_area = area_value # Persist the selection
            
            # Reset assistant so it reloads with area-filtered tools
            self.assistant = None
            
            if on_step:
                await on_step(f"Discovering capabilities for {area_value}...")

            # Deterministic Lookup Table (Bypass LLM for Navigation)
            if area_value == "knowledge_hub":
                try:
                    # Find tool by name (fixed to use KB_ prefixes)
                    domain_tool = next((t for t in self.executor.get_tools() if t.name == "kb_list_domains"), None)
                    if domain_tool:
                        # Call the underlying function
                        domains_str = await domain_tool.func()
                        # Parse "Available Knowledge Domains: HR, General"
                        import re
                        match = re.search(r"Domains: (.*)", domains_str)
                        if match:
                            domains = [d.strip() for d in match.group(1).split(",") if d.strip()]
                            
                            # Domain-specific interactive cues
                            pills = []
                            # Primary Action: Search All
                            pills.append({"label": "🔍 Search Everything", "action": "ask", "value": "I have a general question about everything."})
                            
                            # Domain selection cues
                            for d in domains:
                                pills.append({"label": f"📁 Browse {d}", "action": "ask", "value": f"What information is available in the {d} domain?"})
                            
                            # Specific high-value example cues (Firm Specific)
                            pills.append({"label": "💡 Travel Policy?", "action": "ask", "value": "What is our travel policy?"})
                            pills.append({"label": "💡 Expense Policy?", "action": "ask", "value": "What is our expense policy?"})
                            pills.append({"label": "📅 Holiday Schedule?", "action": "ask", "value": "Show me the holiday schedule for this year."})
                            pills.append({"label": "🛡️ IT Security?", "action": "ask", "value": "What are the password requirements?"})

                            return {
                                "type": "assistant_manifest",
                                "content": "I've connected to the **Armanino Knowledge Hub**. This repository contains firm-wide policies, HR documentation, and business rules.\n\n**You can browse by domain below, use one of the examples, or simply type your question.**",
                                "manifest": {
                                    "componentType": "pills",
                                    "payload": pills
                                }
                            }
                        else:
                            # Fallback if discovery pattern fails
                            return {
                                "type": "assistant_manifest",
                                "content": "I've connected to the **Armanino Knowledge Hub**. How can I help you today? You can ask about firm policies, HR rules, or general information.",
                                "manifest": {
                                    "componentType": "pills",
                                    "payload": [
                                        {"label": "🔍 Search All", "action": "ask", "value": "I have a question."},
                                        {"label": "💡 Expense Policy", "action": "ask", "value": "What is our expense policy?"},
                                        {"label": "📅 Holiday Schedule", "action": "ask", "value": "When is our next holiday?"}
                                    ]
                                }
                            }
                except Exception as e:
                    logger.error(f"Deterministic domain discovery failed: {e}")
                    # Fallback to conversational if tool fails

            elif area_value == "d365":
                return {
                    "type": "assistant_manifest",
                    "content": "**Dynamics 365** integration is active. You can manage sales pipeline and client records. **Select a tool or ask me a client question.**",
                    "manifest": {
                        "componentType": "pills",
                        "payload": [
                            {"label": "🔍 Search for Account", "action": "ask", "value": "I want to search for an account in D365"},
                            {"label": "📋 List Recent Accounts", "action": "ask", "value": "Show me the top 5 accounts in Dynamics 365"},
                            {"label": "🏗️ Create Account", "action": "ask", "value": "I want to create a new client account in Dynamics 365"},
                            {"label": "⤴️ Switch Environment", "action": "ask", "value": "What D365 environments do I have access to?"}
                        ]
                    }
                }

            elif area_value == "workday":
                return {
                    "type": "assistant_manifest",
                    "content": "**Workday** integration is active. You can browse customer accounts and financial data. **Select a tool or ask me about an account.**",
                    "manifest": {
                        "componentType": "pills",
                        "payload": [
                            {"label": "📋 List Accounts", "action": "ask", "value": "Show me all Workday customer accounts"},
                            {"label": "🔍 Find Account", "action": "ask", "value": "I want to find a specific Workday account"},
                            {"label": "📈 Revenue Data", "action": "ask", "value": "Show me revenue data from Workday"}
                        ]
                    }
                }

            elif area_value == "servicenow":
                # Check for existing credentials
                from core.context import auth_user_ctx
                from core.database import AsyncSessionLocal, UserCredential
                from sqlalchemy import select, func
                user_email = auth_user_ctx.get()
                
                async with AsyncSessionLocal() as db:
                    stmt = select(UserCredential).where(
                        UserCredential.service_name == "servicenow",
                        func.lower(UserCredential.user_email) == func.lower(user_email)
                    )
                    result = await db.execute(stmt)
                    cred = result.scalar_one_or_none()

                if not cred:
                    login_url = f"http://localhost:8000/api/v1/servicenow/auth/login?user_email={user_email}"
                    return {
                        "type": "assistant_manifest",
                        "content": "I see you haven't connected your **ServiceNow** account yet. To act on your behalf and respect your permissions, I need you to authorize this connection once.",
                        "manifest": {
                            "componentType": "pills",
                            "payload": [
                                {"label": "🔐 Connect to ServiceNow", "action": "open_url", "value": login_url},
                                {"label": "❓ Why do I need this?", "action": "ask", "value": "Why do I need to connect to ServiceNow?"}
                            ]
                        }
                    }

                return {
                    "type": "assistant_manifest",
                    "content": "**ServiceNow** integration is active. I can now perform actions on your behalf using your developer permissions.\n\n**Common operational tasks:**",
                    "manifest": {
                        "componentType": "pills",
                        "payload": [
                            {"label": "✅ My Approvals", "action": "ask", "value": "Do I have any pending ServiceNow approvals?"},
                            {"label": "🎫 List My Incidents", "action": "ask", "value": "Show my active ServiceNow incidents"},
                            {"label": "🔍 Search KB", "action": "ask", "value": "Search the ServiceNow knowledge base"},
                            {"label": "🆕 Create Incident", "action": "ask", "value": "I need to open a new ServiceNow incident"},
                            {"label": "📋 My Open Tasks", "action": "ask", "value": "Show my assigned ServiceNow tasks"}
                        ]
                    }
                }

            elif area_value == "m365":
                return {
                    "type": "assistant_manifest",
                    "content": "**Microsoft 365 (Graph)** integration is active. I can manage your corporate communications and schedule. **Select a task below:**",
                    "manifest": {
                        "componentType": "pills",
                        "payload": [
                            {"label": "📧 Recent Emails", "action": "ask", "value": "Show my recent emails"},
                            {"label": "📅 List Meetings", "action": "ask", "value": "What's on my calendar for today?"},
                            {"label": "🗓️ Schedule Meeting", "action": "ask", "value": "I want to schedule a new meeting"},
                            {"label": "📁 Search Files", "action": "ask", "value": "Search for a file in my OneDrive"},
                            {"label": "🟢 My Presence", "action": "ask", "value": "What is my current status?"}
                        ]
                    }
                }

            # New agent-based area handlers
            elif area_value == "it_support":
                # Check for existing ServiceNow credentials (same logic as servicenow handler)
                from core.context import auth_user_ctx
                from core.database import AsyncSessionLocal, UserCredential
                from sqlalchemy import select, func
                user_email = auth_user_ctx.get()
                
                async with AsyncSessionLocal() as db:
                    stmt = select(UserCredential).where(
                        UserCredential.service_name == "servicenow",
                        func.lower(UserCredential.user_email) == func.lower(user_email)
                    )
                    result = await db.execute(stmt)
                    cred = result.scalar_one_or_none()

                if not cred:
                    login_url = f"http://localhost:8000/api/v1/servicenow/auth/login?user_email={user_email}"
                    return {
                        "type": "assistant_manifest",
                        "content": "**IT Support Agent** needs ServiceNow access. To manage tickets and approvals on your behalf, I need you to authorize this connection once.",
                        "manifest": {
                            "componentType": "pills",
                            "payload": [
                                {"label": "🔐 Connect to ServiceNow", "action": "open_url", "value": login_url},
                                {"label": "📚 Search Knowledge Hub", "action": "select_area", "value": "knowledge_hub"},
                                {"label": "❓ Why do I need this?", "action": "ask", "value": "Why do I need to connect to ServiceNow?"}
                            ]
                        }
                    }

                config = load_agent_config("it_support")
                return {
                    "type": "assistant_manifest",
                    "content": f"**{config.get('name', 'IT Support Agent')}** is ready to help. {config.get('description', 'I can manage ServiceNow tickets.')}.",
                    "manifest": {
                        "componentType": "pills",
                        "payload": get_agent_pills("it_support")
                    }
                }

            elif area_value == "hr":
                config = load_agent_config("hr")
                return {
                    "type": "assistant_manifest",
                    "content": f"**{config.get('name', 'HR Agent')}** is ready to help. {config.get('description', 'I can assist with time entries and HR questions.')}.",
                    "manifest": {
                        "componentType": "pills",
                        "payload": get_agent_pills("hr")
                    }
                }

            elif area_value == "sales":
                config = load_agent_config("sales")
                return {
                    "type": "assistant_manifest",
                    "content": f"**{config.get('name', 'Sales Agent')}** is ready to help. {config.get('description', 'I can manage CRM data.')}.",
                    "manifest": {
                        "componentType": "pills",
                        "payload": get_agent_pills("sales")
                    }
                }

            elif area_value == "onboarding":
                config = load_agent_config("onboarding")
                return {
                    "type": "assistant_manifest",
                    "content": f"**{config.get('name', 'Client Onboarding Agent')}** is ready to help. {config.get('description', 'I can set up new clients.')}.",
                    "manifest": {
                        "componentType": "pills",
                        "payload": get_agent_pills("onboarding")
                    }
                }

            elif area_value == "pricing_assistant":
                config = load_agent_config("pricing_assistant")
                return {
                    "type": "assistant_manifest",
                    "content": f"**{config.get('name', 'Pricing Assistant')}** is ready to help. {config.get('description', 'I can guide you through pricing and scoping.')}.",
                    "manifest": {
                        "componentType": "pills",
                        "payload": get_agent_pills("pricing_assistant")
                    }
                }

            # If no deterministic match, fallback to conversational (Ferrari mode)
            prompt = f"User selected the area: {area_value}. Please introduce this area and show available tools or categories."
            return await self.process_message(prompt, on_step=on_step)

        try:
            # Execute the tool via local executor (Collapsed BOML)
            result = await self.executor.execute_tool(action, values)
            
            # Extract text content from result
            content_list = []
            if isinstance(result, dict) and "content" in result:
                for item in result["content"]:
                    if item.get("type") == "text":
                        content_list.append(item.get("text", ""))
            
            raw_result = "\n".join(content_list) if content_list else str(result)
            
            # Use formatting pass to summarize the success/failure
            from autogen_agentchat.messages import TextMessage
            messages = [
                TextMessage(content=f"Executed tool: {action} with parameters: {values}", source="user"),
                TextMessage(content=raw_result, source=action)
            ]
            
            manifest_response = await self._format_response(f"Completed form submission for {action}", messages)
            return {
                "type": "assistant_manifest",
                "content": manifest_response.get("content", "Form submission processed."),
                "manifest": manifest_response.get("manifest")
            }
            
        except Exception as e:
            print(f"[Planner] Form tool execution failed: {e}")
            return {"type": "error", "content": f"Failed to execute {action}: {str(e)}"}

    async def _handle_plan_confirmation(self, message: str, values: dict = None) -> dict:
        """Resume a plan from the backend."""
        pending = self.pending_plan
        self.pending_plan = None
        
        is_confirmed = message.lower() in ["yes", "confirm", "ok", "y"]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "X-OpsIQ-Auth-Flow": self.auth_flow
            } if self.auth_token else {}
            ssl_verify = getattr(config, 'SSL_VERIFY', True)
            async with httpx.AsyncClient(verify=ssl_verify) as client:
                payload = {
                    "plan_id": pending["plan_id"],
                    "step_index": pending["step_index"],
                    "context": pending["context"],
                    "confirmation": {
                        "confirmed": is_confirmed,
                        **(values or {})
                    }
                }
                res = await client.post(
                    f"{config.backend_url}/api/v1/plans/resume",
                    json=payload,
                    headers=headers
                )
                res.raise_for_status()
                plan_res = res.json()
                
                if not plan_res.get("success", True):
                    return {"type": "error", "content": plan_res.get("error", "Failed to resume plan.")}

                # In this version, we expect the plan to complete or pause again
                if plan_res.get("status") == "paused":
                    self.pending_plan = {
                        "plan_id": plan_res["plan_id"],
                        "step_index": plan_res["step_index"],
                        "context": plan_res["context"],
                    }
                    hitl = plan_res["confirmation_request"]
                    return {
                        "type": "confirmation_request",
                        "content": hitl["description"],
                        "confirmation_data": hitl["schema"],
                    }
                
                content = plan_res.get("message") or plan_res.get("error", "Plan processed.")
                return {"type": "assistant_message", "content": content}
                
        except Exception as e:
            return {"type": "error", "content": f"Failed to resume plan: {str(e)}"}

    async def _handle_confirmation(self, message: str, values: dict = None) -> dict:
        """Handle confirmation response (Legacy fallback)."""
        pending = self.pending_confirmation
        self.pending_confirmation = None
        
        is_confirmed = message.lower() in ["yes", "confirm", "ok", "y"]
        
        if pending and pending.get("action") == "update_stage" and is_confirmed:
            # Get updated values from front-end if provided (e.g., edited notes)
            notes = values.get("notes") if values else None
            
            # Call the tool directly via executor tools
            for tool in self.executor.get_tools():
                if tool.name == "update_stage":
                    result = await tool._func(
                        client_id=pending["client_id"],
                        new_stage=pending["new_stage"],
                        notes=notes,
                    )
                    return {"type": "assistant_message", "content": result}
        
        return {"type": "system_message", "content": "Action cancelled."}

    def handle_confirmation_response(self, confirmed: bool, values: dict = None) -> dict | None:
        """Handle confirmation from frontend ConfirmationCard."""
        if not self.pending_confirmation:
            return None
        
        pending = self.pending_confirmation
        self.pending_confirmation = None
        
        return {
            "action": pending.get("action"),
            "confirmed": confirmed,
            "data": {**pending, **(values or {})},
        }
