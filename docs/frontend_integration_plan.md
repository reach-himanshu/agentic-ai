# Implementation Plan - Frontend & Orchestrator Integration

This plan finalizes the connection between the AutoGen-powered orchestrator and the React frontend, ensuring all data (including user-edited fields) flows correctly.

## Proposed Changes

### 1. Orchestrator Protocol Alignment
- **File**: `orchestrator/ws_server.py`
- **[MODIFY]**: Update `handle_message` to use `content` instead of `message` in all JSON responses (matches `AgentMessage` TypeScript interface).

### 2. Enhanced HITL (Human-in-the-Loop) Data Flow
- **File**: `orchestrator/agents/planner.py`
- **[MODIFY]**: Update `_handle_confirmation` to accept and utilize optional field values (like `notes`) from the `ConfirmationCard`.
- **File**: `orchestrator/ws_server.py`
- **[MODIFY]**: Pass the `values` from the `confirmation_response` message to the planner.

### 3. Frontend Label Refinement
- **File**: `frontend/src/pages/Chat.tsx`
- **[MODIFY]**: Update connection messages and system prompts to reflect the AutoGen + Azure OpenAI integration if not already clear. (Check existing code reveals it's 90% there, just minor tweaks).

## Verification Plan

### Automated Verification
- Run the orchestrator and use a mock WebSocket client script to verify the new `content` field and confirmation flow with values.

### Manual Verification
1. Start Backend: `uvicorn app.main:app`
2. Start Orchestrator: `python main.py`
3. Launch Frontend: `npm run dev`
4. **Test Case 1**: Ask "Look up Acme Corp". Verify assistant response is displayed.
5. **Test Case 2**: Ask "Update Acme to Qualified". Verify `ConfirmationCard` appears.
6. **Test Case 3**: Edit "Notes" in the card, click "Apply". Verify notes are passed to the backend (check logs).
