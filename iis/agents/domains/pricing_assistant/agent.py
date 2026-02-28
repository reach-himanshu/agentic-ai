"""
Pricing Assistant Agent - Guides sellers through pricing & scoping intake.

This agent implements a multi-phase wizard with conversational fallback:
- Phase 0: CRM Context (pre-fill from D365)
- Phase 1: Core Fields (service line, revenue model, etc.)
- Phase 2: BU Branch (service-specific questions)
- Phase 3: Resourcing (future)
- Phase 4: Compute Price (future - Checkpoint 4)
- Phase 5: Generate Artifacts (future - Checkpoint 5)
"""
from pathlib import Path
from agents.base import DomainAgent, AgentConfig
from .wizard_state import PricingWizardState, WizardPhase
from typing import Dict, Any, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

# Path to config relative to this file
CONFIG_PATH = Path(__file__).parent / "config.yaml"


class PricingAssistantAgent(DomainAgent):
    """
    Pricing Assistant domain agent for guided pricing & scoping intake.
    """
    
    def __init__(self):
        config = AgentConfig.from_yaml(str(CONFIG_PATH))
        super().__init__(config)
        self.d365_mcp = None
        self.wizard_state: Optional[PricingWizardState] = None
    
    async def initialize(self, shared_mcp_registry: dict = None):
        """Load D365 MCP (for CRM context) + shared MCPs."""
        await super().initialize(shared_mcp_registry)
        
        # Load D365 MCP for CRM context (shared with Sales agent)
        try:
            from mcp_registry.d365 import mcp as d365_mcp
            self.d365_mcp = d365_mcp
            self.mcp_instances.append(d365_mcp)
            logger.info("[PricingAssistant] Loaded D365 MCP for CRM context")
        except ImportError as e:
            logger.warning(f"[PricingAssistant] Could not load D365 MCP: {e}")
        
        # Add shared MCPs (KB for policy lookups)
        for name, mcp in self.shared_mcp_registry.items():
            if name in ["kb", "knowledge_hub"]:
                self.mcp_instances.append(mcp)
                logger.info(f"[PricingAssistant] Added shared MCP: {name}")
        
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
                        logger.debug(f"[PricingAssistant] Loaded tool: {tool.name}")
            except Exception as e:
                logger.warning(f"[PricingAssistant] Error loading tools: {e}")
    
    async def load_wizard_state(self, session_id: str, context: dict = None) -> PricingWizardState:
        """
        Load wizard state from context.
        
        State is stored in the context dict that persists across requests.
        """
        # Try to load from context first
        if context and "wizard_state" in context:
            state_dict = context["wizard_state"]
            self.wizard_state = PricingWizardState(**state_dict)
            logger.info(f"[PricingAssistant] Loaded existing wizard state: phase={self.wizard_state.current_phase}, fields={len(self.wizard_state.collected_fields)}")
            return self.wizard_state
        
        # Create new state if not found
        if not self.wizard_state:
            wizard_id = f"pricing_{session_id}_{uuid.uuid4().hex[:8]}"
            self.wizard_state = PricingWizardState.create_new(wizard_id)
            logger.info(f"[PricingAssistant] Created new wizard state: {wizard_id}")
        
        return self.wizard_state
    
    async def save_wizard_state(self, session_id: str, context: dict = None):
        """
        Save wizard state to context.
        
        State is serialized to dict and stored in context for persistence.
        """
        if self.wizard_state and context is not None:
            logger.info(f"[PricingAssistant] save_wizard_state: Before serialization - collected_fields={self.wizard_state.collected_fields}")
            
            # Serialize state to dict
            state_dict = {
                "wizard_id": self.wizard_state.wizard_id,
                "current_phase": self.wizard_state.current_phase.value,
                "collected_fields": self.wizard_state.collected_fields,
                "required_fields_missing": self.wizard_state.required_fields_missing,
                "phase_history": [p.value for p in self.wizard_state.phase_history]
            }
            context["wizard_state"] = state_dict
            
            logger.info(f"[PricingAssistant] Saved wizard state to context: phase={self.wizard_state.current_phase}, fields={len(self.wizard_state.collected_fields)}")
            logger.info(f"[PricingAssistant] Saved state_dict: {state_dict}")
    
    async def process(self, task: str, context: dict) -> dict:
        """
        Process a pricing-related request.
        
        Routes to appropriate wizard phase handler based on current state.
        
        Args:
            task: The user's message/request
            context: Dict containing session_id, user_id, etc.
        
        Returns:
            Dict with 'response', 'manifest', 'type'
        """
        session_id = context.get("session_id", "unknown")
        logger.info(f"[PricingAssistant] process() called with task='{task}', session_id='{session_id}'")
        
        # Load wizard state
        state = await self.load_wizard_state(session_id, context)
        logger.info(f"[PricingAssistant] Loaded state: phase={state.current_phase}, fields={list(state.collected_fields.keys())}")
        
        # Check for special actions
        if "start_wizard" in task or "new pricing request" in task.lower():
            logger.info(f"[PricingAssistant] Detected wizard start command in task: '{task}'")
            return await self._start_wizard(state, context)
        
        if "resume draft" in task.lower():
            return await self._resume_draft(state, context)
        
        # Check for form submission actions
        bu_form_actions = [
            "submit_core_fields",
            "submit_tax_fields",
            "submit_aa_fields",
            "submit_managed_acct_fields",
            "submit_consulting_snow_fields",
            "submit_consulting_d365_fields"
        ]
        
        if task in bu_form_actions:
            logger.info(f"[PricingAssistant] Detected form submission: {task}")
            # Route to appropriate phase handler
            if task == "submit_core_fields":
                return await self._handle_core_fields(task, state, context)
            else:
                # All BU-specific form submissions go to BU branch handler
                return await self._handle_bu_branch(task, state, context)
        
        # Route based on current phase
        if state.current_phase == WizardPhase.NOT_STARTED:
            logger.info("[PricingAssistant] Phase is NOT_STARTED, starting wizard")
            return await self._start_wizard(state, context)
        
        elif state.current_phase == WizardPhase.CRM_CONTEXT:
            return await self._handle_crm_context(task, state, context)
        
        elif state.current_phase == WizardPhase.CORE_FIELDS:
            return await self._handle_core_fields(task, state, context)
        
        elif state.current_phase == WizardPhase.BU_BRANCH:
            return await self._handle_bu_branch(task, state, context)
        
        else:
            # Future phases (Checkpoint 3+)
            return {
                "type": "assistant",
                "content": f"Phase {state.current_phase.value} is not yet implemented. Coming soon in Checkpoint 3!",
                "manifest": None
            }
    
    async def _start_wizard(self, state: PricingWizardState, context: dict) -> dict:
        """
        Start the wizard flow.
        
        Phase 0: CRM Context - try to pre-fill from D365.
        """
        state.transition_to(WizardPhase.CRM_CONTEXT)
        await self.save_wizard_state(context.get("session_id"), context)
        
        # Try to fetch CRM context (if D365 is available)
        crm_data = await self._fetch_crm_context(context)
        
        if crm_data:
            # Pre-fill state with CRM data
            state.set_field("account_name", crm_data.get("account_name"))
            state.set_field("industry", crm_data.get("industry"))
            state.set_field("opportunity_id", crm_data.get("opportunity_id"))
            state.set_field("client_segment", crm_data.get("client_segment"))
            
            # Generate confirmation form
            return {
                "type": "assistant_manifest",
                "content": f"I found your opportunity **{crm_data.get('opportunity_id')}** for **{crm_data.get('account_name')}** ({crm_data.get('industry')}). Is this correct?",
                "manifest": {
                    "componentType": "form",
                    "title": "📋 Confirm CRM Context",
                    "fields": [
                        {"key": "account_name", "label": "Account", "value": crm_data.get("account_name"), "editable": False},
                        {"key": "industry", "label": "Industry", "value": crm_data.get("industry"), "editable": True},
                        {"key": "opportunity_id", "label": "Opportunity ID", "value": crm_data.get("opportunity_id"), "editable": False}
                    ],
                    "submitAction": "confirm_crm_context"
                }
            }
        else:
            # No CRM context available, skip to core fields
            state.transition_to(WizardPhase.CORE_FIELDS)
            await self.save_wizard_state(context.get("session_id"), context)
            return await self._generate_core_fields_form(state)
    
    async def _fetch_crm_context(self, context: dict) -> Optional[Dict[str, Any]]:
        """
        Fetch CRM context from D365 (if available).
        
        For now, returns None. In production, this would call d365_get_opportunity.
        """
        # TODO: Implement D365 integration
        # opportunity_id = context.get("opportunity_id")
        # if opportunity_id and self.d365_mcp:
        #     result = await self.d365_mcp.call_tool("d365_get_opportunity", {"opportunity_id": opportunity_id})
        #     return result
        
        logger.info("[PricingAssistant] CRM context fetch not yet implemented")
        return None
    
    async def _handle_crm_context(self, task: str, state: PricingWizardState, context: dict) -> dict:
        """Handle CRM context confirmation."""
        # User confirmed CRM context, move to core fields
        state.transition_to(WizardPhase.CORE_FIELDS)
        await self.save_wizard_state(context.get("session_id"), context)
        
        return await self._generate_core_fields_form(state)
    
    async def _generate_core_fields_form(self, state: PricingWizardState) -> dict:
        """Generate the core fields form (Phase 1)."""
        return {
            "type": "assistant_manifest",
            "content": "Great! Let's start with the core engagement details.",
            "manifest": {
                "componentType": "form",
                "title": "📋 Core Engagement Details",
                "fields": [
                    {
                        "key": "service_portfolio",
                        "label": "Service Line",
                        "type": "select",
                        "value": state.get_field("service_portfolio", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Tax", "value": "tax"},
                            {"label": "Audit & Assurance", "value": "aa"},
                            {"label": "Managed Accounting", "value": "managed_acct"},
                            {"label": "Consulting (ServiceNow)", "value": "consulting_snow"},
                            {"label": "Consulting (D365)", "value": "consulting_d365"}
                        ]
                    },
                    {
                        "key": "revenue_model",
                        "label": "Revenue Model",
                        "type": "select",
                        "value": state.get_field("revenue_model", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Time & Materials", "value": "tm"},
                            {"label": "Fixed Fee", "value": "fixed"},
                            {"label": "Milestone-Based", "value": "milestone"},
                            {"label": "Retainer / NTE", "value": "retainer"}
                        ]
                    },
                    {
                        "key": "target_date",
                        "label": "Target Delivery Date",
                        "type": "date",
                        "value": state.get_field("target_date", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "legal_entities_count",
                        "label": "Number of Legal Entities",
                        "type": "number",
                        "value": state.get_field("legal_entities_count", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "geographies",
                        "label": "Geographies (comma-separated)",
                        "type": "text",
                        "value": state.get_field("geographies", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "e.g., US-CA, US-TX, UK"
                    }
                ],
                "submitAction": "submit_core_fields"
            }
        }
    
    async def _handle_core_fields(self, task: str, state: PricingWizardState, context: dict) -> dict:
        """Handle Phase 1: Core Fields."""
        from .phases.core_fields import handle_core_fields_phase
        
        # Call the phase handler
        result = await handle_core_fields_phase(task, state, context)
        
        # CRITICAL: Always save state after fields are processed (fixes collected_fields persistence bug)
        await self.save_wizard_state(context.get("session_id"), context)
        logger.info(f"[PricingAssistant] _handle_core_fields: State saved after processing, collected_fields={list(state.collected_fields.keys())}")
        
        # Check if we need to transition to BU branch
        if result.get("type") == "transition_to_bu_branch":
            # Transition to BU branch phase
            state.transition_to(WizardPhase.BU_BRANCH)
            await self.save_wizard_state(context.get("session_id"), context)
            
            # Generate BU-specific form (clear values to avoid false submission detection)
            bu_context = {k: v for k, v in context.items() if k != "values"}
            return await self._handle_bu_branch(task, state, bu_context)
        
        return result
    
    async def _generate_servicenow_form(self, state: PricingWizardState) -> dict:
        """Generate ServiceNow scope form (Phase 2 - BU Branch)."""
        return {
            "type": "assistant_manifest",
            "content": "Now, let's dive into the ServiceNow engagement scope.",
            "manifest": {
                "componentType": "form",
                "title": "🛠️ ServiceNow Engagement Scope",
                "fields": [
                    {
                        "key": "modules",
                        "label": "Modules in Scope",
                        "type": "multiselect",
                        "value": state.get_field("modules", []),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "IT Service Management (ITSM)", "value": "itsm"},
                            {"label": "IT Operations Management (ITOM)", "value": "itom"},
                            {"label": "HR Service Delivery (HRSD)", "value": "hrsd"},
                            {"label": "Customer Service Management (CSM)", "value": "csm"}
                        ]
                    },
                    {
                        "key": "user_count",
                        "label": "Total User Count",
                        "type": "number",
                        "value": state.get_field("user_count", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "Total named users who will access the platform"
                    },
                    {
                        "key": "customizations_score",
                        "label": "Customization Complexity (1-5)",
                        "type": "select",
                        "value": state.get_field("customizations_score", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "1 - Minimal (OOTB)", "value": 1},
                            {"label": "2 - Light (Minor Config)", "value": 2},
                            {"label": "3 - Moderate (Custom Workflows)", "value": 3},
                            {"label": "4 - Heavy (Custom Apps)", "value": 4},
                            {"label": "5 - Extensive (Platform Extension)", "value": 5}
                        ]
                    },
                    {
                        "key": "integration_endpoints",
                        "label": "Number of Integrations",
                        "type": "number",
                        "value": state.get_field("integration_endpoints", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "hypercare_weeks",
                        "label": "Hypercare Duration (weeks)",
                        "type": "number",
                        "value": state.get_field("hypercare_weeks", 4),
                        "editable": True,
                        "required": True
                    }
                ],
                "submitAction": "submit_snow_scope"
            }
        }
    
    async def _handle_bu_branch(self, task: str, state: PricingWizardState, context: dict) -> dict:
        """Handle Phase 2: BU-Specific Branch."""
        from .phases.bu_branch import handle_bu_branch_phase
        
        # Call the phase handler
        result = await handle_bu_branch_phase(task, state, context)
        
        # CRITICAL: Always save state after fields are processed (fixes collected_fields persistence bug)
        await self.save_wizard_state(context.get("session_id"), context)
        logger.info(f"[PricingAssistant] _handle_bu_branch: State saved after processing, collected_fields={list(state.collected_fields.keys())}")
        
        return result
    
    async def _extract_core_fields_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract structured core fields from conversational text.
        
        For now, uses simple keyword matching. In production, would use LLM.
        """
        extracted = {}
        
        text_lower = text.lower()
        
        # Service portfolio detection
        if "servicenow" in text_lower or "snow" in text_lower:
            extracted["service_portfolio"] = "consulting_snow"
        elif "d365" in text_lower or "dynamics" in text_lower:
            extracted["service_portfolio"] = "consulting_d365"
        elif "tax" in text_lower:
            extracted["service_portfolio"] = "tax"
        
        # Revenue model detection
        if "fixed fee" in text_lower or "fixed price" in text_lower:
            extracted["revenue_model"] = "fixed"
        elif "t&m" in text_lower or "time and materials" in text_lower:
            extracted["revenue_model"] = "tm"
        
        # User count extraction (simple regex)
        import re
        user_match = re.search(r'(\d+)\s*users?', text_lower)
        if user_match:
            extracted["user_count"] = int(user_match.group(1))
        
        # Integration count
        integration_match = re.search(r'(\d+)\s*integrations?', text_lower)
        if integration_match:
            extracted["integration_endpoints"] = int(integration_match.group(1))
        
        logger.info(f"[PricingAssistant] Extracted fields from text: {extracted}")
        return extracted
    
    async def _resume_draft(self, state: PricingWizardState, context: dict) -> dict:
        """Resume a draft pricing request."""
        if state.current_phase == WizardPhase.NOT_STARTED:
            return {
                "type": "assistant",
                "content": "You don't have any draft pricing requests. Click **🆕 New Pricing Request** to start!",
                "manifest": None
            }
        
        # Resume from current phase
        return {
            "type": "assistant",
            "content": f"Resuming your draft from **{state.current_phase.value}** phase...",
            "manifest": None
        }
