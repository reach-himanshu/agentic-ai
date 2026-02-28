"""
AutoGen-based Planner Agent for workflow orchestration with HITL.
"""
import httpx
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from agents.executor import ExecutorAgent
from config import config


class PlannerAgent:
    """
    Planner agent for orchestrating workflows with HITL confirmation.
    Uses AutoGen 0.7.x agents to process requests and call tools.
    """
    
    def __init__(self, executor: ExecutorAgent):
        self.executor = executor
        self.pending_confirmation: dict | None = None
        self.pending_plan: dict | None = None
        self.auth_token: str | None = None
        
        # Initialize HTTP Client - use SSL_VERIFY from config, default to True for security
        ssl_verify = getattr(config, 'SSL_VERIFY', True)
        self.http_client = httpx.AsyncClient(verify=ssl_verify)
        self.model_client = None
        self.assistant = None
        self._active_model = None
        
        # Default to the first available model
        self.switch_model()

    def switch_model(self, model_id: str = None):
        """Switch the active LLM model."""
        model_def = config.get_model(model_id)
        if not model_def:
            print(f"[Planner] Model {model_id} not found, using default.")
            return

        print(f"[Planner] Switching to model: {model_def.name} ({model_def.provider})")
        self._active_model = model_def
        
        if model_def.provider == "local":
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
        else:
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
        
        # Re-initialize the assistant with the new model client, dynamic tools and persona context
        persona_prefix = ""
        if hasattr(self, "user_name") and self.user_name:
            persona_name = "Executive Administrator" if "APP_ROLE_ADMIN" in self.user_roles else "Business User"
            persona_prefix = f"You are acting as {persona_name} ({self.user_name}).\n"
            if persona_name == "Business User":
                persona_prefix += "You have read-only access to business data. You can list and look up information but cannot perform creates or updates.\n"
        
        self.assistant = AssistantAgent(
            name="planner_assistant",
            model_client=self.model_client,
            system_message=f"""{persona_prefix}You are a premium AI Orchestrator for Ops IQ.
            Your goal is to guide users through business automations across Dynamics 365, Workday, and ServiceNow.
            
            GUIDANCE & DISCOVERY:
            - If the user is at the start of a session or seems unsure, offer "Area" selection pills (e.g., "Dynamics 365", "Workday", "ServiceNow", "Armanino Knowledge Hub").
            - Prioritize the **Armanino Knowledge Hub** for general firm-wide inquiries or when the user is looking for documentation/policies.
            - Once an area is selected, suggest relevant "Tool" pills (e.g., "List Accounts", "Create Opportunity", "Search Knowledge Base").
            - Use pills to make it easy for users to discover and trigger capabilities.
            
            FORMATTING GUIDELINES:
            - When presenting lists of items, ALWAYS use clear markdown formatting (tables or lists).
            - Use bold text for key fields.
            
            Your responses are processed by a UI Manifest Generator. 
            Be concise and helpful.""",
            tools=self.executor.get_tools(),
        )

    def set_persona(self, name: str, roles: list[str]):
        """Set user persona context."""
        self.user_name = name
        self.user_roles = roles

    @property
    def model_info(self) -> str:
        """Get human-readable model information from current client."""
        if self._active_model:
            hosting = "Cloud" if self._active_model.provider == "azure" else "Local"
            return f"{hosting} - {self._active_model.name}"
        return "Active Model"

    def set_auth_info(self, token: str, flow: str = "CLIENT_CREDENTIALS"):
        """Set authentication token and flow preference for backend requests."""
        self.auth_token = token
        self.auth_flow = flow

    async def _get_intent(self, message: str) -> dict:
        """Use LLM to detect user intent and extract parameters."""
        prompt = f"""
        Analyze the user message and determine the intent.
        
        Available Intents:
        1. update_client_stage: The user wants to update a client's pipeline stage (e.g., "Move Acme to qualified", "Update stage for Global Tech").
        2. general_query: Anything else (greetings, general questions, requests for info).
        
        If the intent is 'update_client_stage', extract:
        - client_name: The name of the client (e.g., "Acme Corp"). Try to normalize common names.
        - new_stage: The target stage. Use EXACTLY one of these: prospect, qualified, negotiation, closed_won, closed_lost. (Convert "Closed Won" to "closed_won").
        
        Return JSON format: {{"intent": "update_client_stage", "parameters": {{"client_name": "Acme", "new_stage": "qualified"}}}}
        If general, return: {{"intent": "general_query", "parameters": {{}}}}
        
        User Message: "{message}"
        """
        
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
    ) -> dict:
        """Process a user message using AutoGen agents."""
        
        # Check if this is a confirmation response
        if self.pending_plan:
            return await self._handle_plan_confirmation(user_message, values)
        
        if self.pending_confirmation:
            return await self._handle_confirmation(user_message, values)
        
        # Enhanced Intent Detection
        intent_data = await self._get_intent(user_message)
        print(f"[Planner] Intent Data: {intent_data}")
        
        if intent_data.get("intent") == "update_client_stage":
            params = intent_data.get("parameters", {})
            return await self._handle_stage_update_hitl(
                user_message, 
                client_name=params.get("client_name"),
                new_stage=params.get("new_stage")
            )

        # For simple lookups or general queries, use the AutoGen agent
        try:
            print(f"[Planner] Running agent task: {user_message}")
            result = await self.assistant.run(task=user_message)
            
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

    async def _format_response(self, task: str, messages: list) -> dict:
        """
        Final pass to format the agent's output into a UI Manifest.
        """
        # Prepare context for the formatting model
        history = []
        for msg in messages:
            # Source can be 'planner_assistant' or tool names
            source = getattr(msg, "source", "unknown")
            content = getattr(msg, "content", "")
            if content:
                history.append(f"[{source}]: {content}")
        
        history_str = "\n".join(history)
        
        prompt = f"""
        You are a UI Manifest Generator. Your job is to transform raw agent execution history into a structured UI Manifest for a premium React frontend.
        
        Task: {task}
        
        Execution History:
        {history_str}
        
        Available Components:
        1. 'pills': Use to provide a list of options/actions. Payload: [{{ "label": "Dynamics 365", "action": "select_area", "value": "d365" }}]. Use this for initial area discovery or tool suggestions.
        2. 'table': Use for lists of objects (accounts, opportunities, clients). Most common for search results.
        3. 'form': Use when the user wants to CREATE or UPDATE something, but the agent needs confirmation or more details.
        4. 'hero': Use for a single high-impact result (e.g., a specific client lookup with detailed fields).
        5. 'markdown': Use if no structured component is needed.
        
        The 'pills' payload is a list of options: [{{ "label": "Create Account", "action": "click", "value": "create_account" }}].
        The 'table' payload should be a list of objects.
        The 'form' payload should be: {{ "title": "Create Account", "fields": [ {{ "key": "name", "label": "Account Name", "value": "Global Tech", "editable": true }} ], "submitAction": "d365_create_account" }}
        
        Output Format (JSON):
        {{
            "content": "A friendly text summary of what happened.",
            "manifest": {{
                "componentType": "pills" | "table" | "form" | "hero" | "markdown",
                "payload": <the data for the component>
            }}
        }}
        
        Return ONLY the JSON. No markdown code blocks.
        """
        
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

    async def handle_form_response(self, action: str, values: dict) -> dict:
        """Handle a direct form submission by executing the corresponding tool."""
        print(f"[Planner] Handling form submission for action: {action}")
        
        try:
            # Execute the tool via MCP client
            result = await self.executor.mcp_client.execute_tool(action, values)
            
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
