"""
Plan executor service for YAML-based workflow plans.
"""
import yaml
from pathlib import Path
from typing import Any
from pydantic import BaseModel

from app.middleware.auth import TokenData


class PlanStep(BaseModel):
    """A single step in a plan."""
    id: str
    action: str
    description: str | None = None
    input_mapping: dict[str, str] | None = None
    output_variable: str | None = None
    condition: str | None = None
    on_condition_false: dict | None = None
    requires_confirmation: bool = False
    required_roles: list[str] | None = None
    
    # Allow extra fields for dynamic YAML content (rule, schema, etc)
    class Config:
        extra = "allow"


class Plan(BaseModel):
    """A complete execution plan."""
    plan_id: str
    name: str
    description: str | None = None
    required_roles: list[str] = []
    steps: list[PlanStep]


class PlanExecutor:
    """
    Loads and executes YAML-based plans.
    """
    
    def __init__(self, plans_dir: str = "plans"):
        self.plans_dir = Path(plans_dir)
        self.plans: dict[str, Plan] = {}
        self._load_plans()
    
    def _load_plans(self):
        """Load all plan files from the plans directory."""
        if not self.plans_dir.exists():
            return
        
        for plan_file in self.plans_dir.glob("*.yaml"):
            try:
                with open(plan_file, "r") as f:
                    data = yaml.safe_load(f)
                    plan = Plan(**data)
                    self.plans[plan.plan_id] = plan
            except Exception as e:
                print(f"Error loading plan {plan_file}: {e}")
    
    def get_plan(self, plan_id: str) -> Plan | None:
        """Get a plan by ID."""
        return self.plans.get(plan_id)
    
    def list_plans(self) -> list[dict]:
        """List all available plans."""
        return [
            {
                "plan_id": p.plan_id,
                "name": p.name,
                "description": p.description,
                "required_roles": p.required_roles,
                "step_count": len(p.steps),
            }
            for p in self.plans.values()
        ]
    
    def check_permissions(self, plan: Plan, user: TokenData) -> bool:
        """Check if user has required roles for a plan."""
        if not plan.required_roles:
            return True
        
        user_roles = set(user.roles)
        required = set(plan.required_roles)
        return bool(user_roles.intersection(required))
    
    def _resolve_template(self, data: Any, context: dict[str, Any]) -> Any:
        """Resolve {{var}} templates recursively in strings, lists, and dicts."""
        if isinstance(data, list):
            return [self._resolve_template(item, context) for item in data]
        if isinstance(data, dict):
            return {k: self._resolve_template(v, context) for k, v in data.items()}
        if not isinstance(data, str):
            return data
            
        import re
        
        def replacer(match):
            path_parts = match.group(1).strip().split('.')
            val = context
            for key in path_parts:
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    return match.group(0) # Return original if not found
            return str(val) if val is not None else ""
            
        return re.sub(r'\{\{(.*?)\}\}', replacer, data)

    def _resolve_mapping(self, target_mapping: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Resolve a whole dictionary of templates."""
        return self._resolve_template(target_mapping, context)

    async def execute_step(
        self,
        step: PlanStep,
        context: dict[str, Any],
        user: TokenData,
    ) -> dict[str, Any]:
        """Execute a single plan step."""
        # Check step-level permissions
        if step.required_roles:
            if not set(user.roles).intersection(set(step.required_roles)):
                return {
                    "step_id": step.id,
                    "success": False,
                    "error": f"Insufficient permissions for step. Required: {step.required_roles}",
                }

        # 1. Resolve Inputs
        print(f"DEBUG: step.id={step.id}, input_mapping={step.input_mapping}")
        
        mapping_to_resolve = step.input_mapping if step.input_mapping is not None else {}
        resolved_inputs = self._resolve_mapping(mapping_to_resolve, context)
        
        print(f"[PlanExecutor] Executing step '{step.id}' (action: {step.action})")
        print(f"[PlanExecutor] Resolved Inputs: {resolved_inputs}")
        
        # 2. Execute Action
        step_dict = step.model_dump()
        result = {"success": True, "step_id": step.id, "description": step.description or ""}
        
        if step.action == "mcp_tool":
            from app.tools.update_stage import update_stage_tool
            from app.tools.lookup_client import lookup_client_tool
            
            tool_name = step_dict.get("tool", step.id)
            print(f"[PlanExecutor] Using tool: {tool_name}")
            if tool_name == "lookup_client":
                res = await lookup_client_tool(user, **resolved_inputs)
                result.update(res)
            elif tool_name == "update_stage":
                res = await update_stage_tool(user, **resolved_inputs)
                result.update(res)
        
        elif step.action == "validate_rule":
            # State machine validation
            rule = step_dict.get("rule")
            
            if rule and rule.get("type") == "state_machine":
                # Look into the 'client' sub-dict of the previous output variable
                client_data_res = context.get("client_data", {})
                current_stage = str(client_data_res.get("client", {}).get("stage", ""))
                new_stage = resolved_inputs.get("new_stage")
                allowed = rule.get("allowed_transitions", {}).get(current_stage, [])
                
                print(f"[PlanExecutor] Validating transition: {current_stage} -> {new_stage}")
                if new_stage not in allowed:
                    print(f"[PlanExecutor] Validation failed: {new_stage} not in {allowed}")
                    return {
                        "success": False,
                        "error": f"Invalid transition from {current_stage} to {new_stage}. Allowed: {allowed}"
                    }
        
        # Check condition if present (simplistic evaluates-to-true check for the POC)
        condition = step_dict.get("condition")
        if condition:
            resolved_cond = self._resolve_template(condition, context)
            print(f"[PlanExecutor] Checking condition: {condition} -> {resolved_cond}")
            # Very basic string comparison for 'true' or 'True'
            if resolved_cond.lower() != "true":
                print(f"[PlanExecutor] Condition not met. Branching.")
                on_false = step_dict.get("on_condition_false", {})
                if on_false and "next_step" in on_false:
                    # In a real engine we'd jump to next_step, for now we just cancel
                    return {"success": True, "step_id": step.id, "message": "Condition not met, stopping."}
        
        elif step.action == "generative_ui":
            print(f"[PlanExecutor] Preparing UI schema")
            result["type"] = "confirmation_request"
            
            # Combine current step inputs and overall context for schema resolution
            schema_context = {**context, "input": resolved_inputs}
            result["schema"] = self._resolve_template(step_dict.get("schema", {}), schema_context)
            
            if step_dict.get("requires_confirmation", False):
                result["requires_confirmation"] = True
                print(f"[PlanExecutor] Step requires confirmation")

        # Handle explicit 'respond' action
        elif step.action == "respond":
            msg_tmpl = step_dict.get("message", "Plan step executed.")
            result["message"] = self._resolve_template(msg_tmpl, context)
            print(f"[PlanExecutor] Respondent message: {result['message']}")

        if step.output_variable:
            context[step.output_variable] = result
            
        return result

    async def run_plan(
        self,
        plan_id: str,
        initial_input: dict[str, Any],
        user: TokenData,
    ) -> dict[str, Any]:
        """Run a plan from the beginning."""
        plan = self.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": f"Plan {plan_id} not found"}
        
        if not self.check_permissions(plan, user):
            return {"success": False, "error": "Permission denied for this plan"}

        context = {
            "input": initial_input,
            "user": {"name": user.name, "roles": user.roles},
            "_plan_id": plan_id,
        }
        
        # In a real app, we'd store the session in a DB
        # For this prototype, we'll return the current state if a pause is needed
        return await self._execute_from_step(plan, 0, context, user)

    async def _execute_from_step(
        self,
        plan: Plan,
        start_index: int,
        context: dict[str, Any],
        user: TokenData,
    ) -> dict[str, Any]:
        """Iterate through steps starting from index."""
        current_index = start_index
        
        while current_index < len(plan.steps):
            step = plan.steps[current_index]
            
            # Execute the step
            result = await self.execute_step(step, context, user)
            print(f"[PlanExecutor] Step '{step.id}' result: {result}")
            
            if not result.get("success"):
                return result
            
            # If HITL required, pause and return current state
            if result.get("requires_confirmation") or result.get("type") == "confirmation_request":
                print(f"[PlanExecutor] Pausing for HITL at step '{step.id}'")
                return {
                    "status": "paused",
                    "plan_id": plan.plan_id,
                    "step_index": current_index,
                    "context": context,
                    "confirmation_request": {
                        "description": result.get("description", ""),
                        "schema": result.get("schema", {})
                    }
                }
            
            # Move to next step (handle condition branching here if needed)
            # Simple linear execution for now, but stop if we hit a 'respond' action
            if step.action == "respond" or result.get("message") == "Condition not met, stopping.":
                break
                
            current_index += 1
            
        return {
            "status": "completed",
            "plan_id": plan.plan_id,
            "final_context": context,
            "message": f"Plan '{plan.name}' completed successfully"
        }

    async def resume_plan(
        self,
        plan_id: str,
        step_index: int,
        context: dict[str, Any],
        confirmation_data: dict[str, Any],
        user: TokenData,
    ) -> dict[str, Any]:
        """Resume a plan after a pause (e.g. HITL)."""
        plan = self.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": f"Plan {plan_id} not found"}
        
        # Inject confirmation data into context
        context["confirmation"] = confirmation_data
        
        # Resume from the NEXT step
        return await self._execute_from_step(plan, step_index + 1, context, user)


# Global executor instance
plan_executor = PlanExecutor()
