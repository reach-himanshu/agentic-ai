"""
Router for YAML-based execution plans.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from app.middleware.auth import get_current_user, TokenData
from app.services.plan_executor import plan_executor

router = APIRouter()


@router.get("/", response_model=list[dict])
async def list_plans(user: TokenData = Depends(get_current_user)):
    """List all available plans."""
    return plan_executor.list_plans()


@router.get("/{plan_id}")
async def get_plan(plan_id: str, user: TokenData = Depends(get_current_user)):
    """Get plan details."""
    plan = plan_executor.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found"
        )
    return plan


@router.post("/{plan_id}/execute")
async def execute_plan(
    plan_id: str,
    input_data: dict[str, Any],
    user: TokenData = Depends(get_current_user)
):
    """Start execution of a plan."""
    return await plan_executor.run_plan(plan_id, input_data, user)


@router.post("/resume")
async def resume_plan(
    payload: dict[str, Any],
    user: TokenData = Depends(get_current_user)
):
    """Resume a plan from a specific step."""
    plan_id = payload.get("plan_id")
    step_index = payload.get("step_index")
    context = payload.get("context")
    confirmation = payload.get("confirmation")
    
    if plan_id is None or step_index is None or context is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: plan_id, step_index, context"
        )
        
    return await plan_executor.resume_plan(
        plan_id, step_index, context, confirmation, user
    )
