import json
import asyncio
from typing import List, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent
from core.database import init_db, get_db, ChatSession
from core.observability import setup_observability
from sqlalchemy import select
from contextlib import asynccontextmanager

# Import Routers from BOML
from integrations.d365.router import router as d365_router
from integrations.workday.router import router as workday_router
from integrations.servicenow.router import router as servicenow_router

import logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize observability
    setup_observability()
    # Initialize database (optional for dev without containers)
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"[IIS] Database init failed (Postgres not running?): {e}")
        logger.warning("[IIS] Running in limited mode - session persistence disabled")
    yield

# Initialize FastAPI App
app = FastAPI(
    title="Ops IQ: Integrated Intelligence Service (IIS)",
    version="2.0.0",
    description="Unified Orchestration, Mediation, and Tool execution layer.",
    docs_url=None, 
    redoc_url=None,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (for Swagger UI)
import os
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Custom Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "iis"}

# --- Admin Endpoints ---

@app.post("/admin/reload-prompts")
async def reload_prompts():
    """Hot-reload all YAML prompt templates from disk without restarting the server."""
    from core.prompt_manager import prompts
    prompts.reload()
    available = prompts.list_prompts()
    return {
        "status": "success",
        "message": f"Reloaded {len(available)} prompts",
        "prompts": available
    }

@app.get("/admin/prompts")
async def list_prompts():
    """List all available prompt templates."""
    from core.prompt_manager import prompts
    return {"prompts": prompts.list_prompts()}


# --- Agent Discovery (Modular Agent Architecture) ---

class AgentCatalogRequest(BaseModel):
    roles: List[str] = []

@app.post("/api/v1/agents")
async def get_available_agents(request: AgentCatalogRequest):
    """
    Return list of agents the user has access to based on their roles.
    
    Roles come from Azure App Roles in the JWT token.
    """
    from agents.entitlements import get_agent_catalog, has_app_access
    
    if not has_app_access(request.roles):
        return {
            "available": [],
            "locked": [],
            "error": "No app access. Missing OpsIQ.User role."
        }
    
    return get_agent_catalog(request.roles)


# Include BOML Routers
app.include_router(d365_router, prefix="/api/v1/d365", tags=["D365"])
app.include_router(workday_router, prefix="/api/v1/workday", tags=["Workday"])
app.include_router(servicenow_router, prefix="/api/v1/servicenow", tags=["ServiceNow"])

# --- Model Discovery ---

@app.get("/api/v1/models/")
async def get_models():
    """Return list of available models for the frontend selector."""
    models = await config.get_available_models()
    return [{
        "id": m.id,
        "name": m.name,
        "provider": m.provider,
        "available": True # config.get_available_models already filters for available
    } for m in models]
    
# --- Stateless Chat API ---

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    user_email: str | None = None
    content: str
    model_id: str | None = None
    auth_token: str | None = None
    auth_flow: str | None = "CLIENT_CREDENTIALS"
    name: str | None = None
    roles: List[str] = []
    action: str | None = None
    values: dict = {}

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Stateless chat endpoint that persists agent state to the database."""
    from core.session_store import SessionStore
    store = SessionStore(db)
    
    # Get or create database session
    db_session = await store.get_or_create_session(request.session_id, request.user_id, request.model_id)
    
    # Initialize agents (Orchestrator singleton-like behavior per request)
    executor = ExecutorAgent(None)
    await executor.initialize_tools()
    planner = PlannerAgent(executor)
    
    # Set model and auth
    if request.model_id:
        planner.switch_model(request.model_id)
    if request.auth_token:
        await planner.set_auth_info(request.auth_token, request.auth_flow, user_id=request.user_id, email=request.user_email, roles=request.roles)
    if request.name:
        planner.set_persona(request.name, request.roles)
        
    # Re-hydrate state from DB
    if db_session.state:
        await planner.load_state(db_session.state)
        
    # Process Message
    if request.action:
        # Direct tool execution/form response
        response = await planner.handle_form_response(request.action, request.values)
    else:
        # Standard NLP processing
        response = await planner.process_message(request.content)
    
    # Persist message to history
    await store.add_message(request.session_id, "user", request.content, msg_type="user")
    await store.add_message(
        request.session_id, 
        "assistant", 
        response.get("content", ""), 
        msg_type=response.get("type", "assistant_message"),
        manifest=response.get("manifest")
    )
    
    # Save updated state
    new_state = await planner.save_state()
    await store.save_agent_state(request.session_id, new_state)
    
    return response

@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """SSE Streaming chat endpoint for real-time transparency."""
    from sse_starlette.sse import EventSourceResponse
    from core.session_store import SessionStore
    store = SessionStore(db)

    async def event_generator():
        # 1. Initialize Agents
        from core.context import auth_user_ctx
        executor = ExecutorAgent(None)
        await executor.initialize_tools()
        planner = PlannerAgent(executor)
        
        logger.info(f"[SSE] Starting stream for session {request.session_id}, user {request.user_id}")
        
        if request.auth_token:
            await planner.set_auth_info(request.auth_token, request.auth_flow, user_id=request.user_id, email=request.user_email, roles=request.roles)
            logger.info(f"[SSE] Context set: auth_user_ctx={auth_user_ctx.get()}")

        if request.name:
            planner.set_persona(request.name, request.roles)

        # 2. Get/Create Session & Load State
        db_session = await store.get_or_create_session(request.session_id, request.user_id, request.model_id)
        planner.set_session_id(request.session_id)  # Set session ID for state persistence
        if db_session.state:
            await planner.load_state(db_session.state)

        # 3. Define Step Callback
        # 4. Process Message
        try:
            yield {"event": "reasoning", "data": json.dumps({"type": "reasoning", "stage": "orchestration", "status": "in_progress", "message": "Starting agent session"})}

            # Define a queue to capture thoughts from the callback
            thought_queue = asyncio.Queue()

            async def on_step_cb(content: str):
                await thought_queue.put(content)

            # Run processing in a task so we can yield from the queue
            async def run_processor():
                try:
                    if request.action:
                        res = await planner.handle_form_response(request.action, request.values, on_step=on_step_cb)
                    else:
                        res = await planner.process_message(request.content, on_step=on_step_cb)
                    await thought_queue.put(None) # Signal completion
                    return res
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    await thought_queue.put(e)
                    return None

            processor_task = asyncio.create_task(run_processor())

            while True:
                thought = await thought_queue.get()
                if thought is None: # Success
                    logger.info("[SSE] Thought queue completed (None received)")
                    break
                if isinstance(thought, Exception):
                    raise thought
                
                # Handle both legacy string and structured reasoning events
                if isinstance(thought, dict) and thought.get("type") == "reasoning":
                    logger.info(f"[SSE] Yielding reasoning: {thought.get('stage')} - {thought.get('message', '')[:30]}...")
                    yield {
                        "event": "reasoning",
                        "data": json.dumps(thought)
                    }
                else:
                    thought_str = thought if isinstance(thought, str) else str(thought)
                    logger.info(f"[SSE] Yielding thought: {thought_str[:50]}...")
                    yield {
                        "event": "thought",
                        "data": json.dumps({"content": thought_str})
                    }
                # Small delay to force network buffer flush for progressive streaming
                await asyncio.sleep(0.01)

            response = await processor_task
            logger.info(f"[SSE] Processor task completed for session {request.session_id}")
            
            if not response:
                logger.error("[SSE] Processor task returned no response")
                raise Exception("Agent failed to respond")

            # 5. Persist Interaction
            await store.add_message(request.session_id, "user", request.content, msg_type="user")
            await store.add_message(
                request.session_id, 
                "assistant", 
                response.get("content", ""), 
                msg_type=response.get("type", "assistant_message"),
                manifest=response.get("manifest")
            )
            
            # Save final state
            new_state = await planner.save_state()
            await store.save_agent_state(request.session_id, new_state)

            # 6. Yield Final Message IMMEDIATELY to close the SSE stream for the client.
            # This must happen before any blocking operations like title generation.
            yield {
                "event": "message",
                "data": json.dumps(response)
            }

            # 7. Generate Title (fire-and-forget after response is sent)
            # This is non-blocking for the user experience.
            if db_session.title == "New Chat":
                new_title = await planner.generate_title(request.content, response.get("content", ""))
                await store.update_session_title(request.session_id, new_title)
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({"content": f"Streaming Error: {str(e)}"})
            }

    # Configure SSE with settings to prevent buffering
    return EventSourceResponse(
        event_generator(),
        ping=5,  # Send ping every 5 seconds to keep connection alive
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",  # Disable nginx buffering if behind proxy
            "Connection": "keep-alive"
        }
    )

@app.get("/api/v1/chat/{session_id}/history")
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch chat history for a session from the database."""
    from core.session_store import SessionStore
    store = SessionStore(db)
    messages = await store.get_history(session_id)
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "type": m.type,
            "manifest": m.manifest,
            # Force UTC offset suffix for consistent frontend parsing
            "timestamp": m.created_at.isoformat() if m.created_at.tzinfo else m.created_at.isoformat() + "+00:00"
        } for m in messages
    ]

@app.get("/api/v1/sessions")
async def list_sessions(user_id: str, db: AsyncSession = Depends(get_db)):
    """List all recent chat sessions for a user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "model_id": s.model_id,
            # Force UTC offset suffix for consistent frontend parsing
            "updated_at": s.updated_at.isoformat() if s.updated_at.tzinfo else s.updated_at.isoformat() + "+00:00",
        } for s in sessions
    ]

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific chat session and all its messages."""
    from core.session_store import SessionStore
    store = SessionStore(db)
    success = await store.delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or not owned by user")
    return {"status": "success", "message": f"Session {session_id} deleted"}

# --- WebSocket & Agent Orchestration ---

class ConnectionManager:
    """Manages active WebSocket connections and their agent sessions."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.sessions: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Initialize session with agents
        # Note: ExecutorAgent will be refactored to use local tools
        # For now, we pass None as mcp_client since we'll call local
        executor = ExecutorAgent(None) 
        planner = PlannerAgent(executor)
        
        self.sessions[websocket] = {
            "executor": executor,
            "planner": planner,
            "auth_token": None,
        }
        
        print(f"[IIS] Client connected. Active sessions: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.sessions:
            del self.sessions[websocket]
        print(f"[IIS] Client disconnected. Remaining sessions: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial connection greeting
    await manager.send_message(websocket, {
        "type": "system_message",
        "content": "Connected to Integrated Intelligence Service (IIS) • Authenticate to continue",
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            session = manager.sessions.get(websocket)
            if not session:
                continue

            msg_type = data.get("type")
            
            # Handle Auth Flow
            if msg_type == "auth":
                token = data.get("token")
                model_id = data.get("model_id")
                
                # Check for duplicate auth (resilient against React re-mounts)
                if session.get("authenticated") and session.get("auth_token") == token and session.get("model_id") == model_id:
                    print("[IIS] Ignoring duplicate auth request for session.")
                    continue

                # Update session
                session["auth_token"] = token
                session["model_id"] = model_id
                session["authenticated"] = True
                
                # Extract persona
                user_name = data.get("name")
                user_roles = data.get("roles", [])
                
                # Initialize local tools (Executor refactor pending)
                executor: ExecutorAgent = session["executor"]
                await executor.initialize_tools()
                
                # Update planner
                planner: PlannerAgent = session["planner"]
                user_id = data.get("user_id")
                user_email = data.get("email") or data.get("user_email")
                await planner.set_auth_info(token, data.get("auth_flow", "CLIENT_CREDENTIALS"), user_id=user_id, email=user_email, roles=user_roles)
                if hasattr(planner, "set_persona"):
                    planner.set_persona(user_name, user_roles)
                
                # Switch model
                if model_id:
                    planner.switch_model(model_id)
                else:
                    planner.switch_model(planner._active_model.id if planner._active_model else None)
                
                await manager.send_message(websocket, {
                    "type": "auth_success", 
                    "content": "Authenticated with Integrated Agents",
                    "model_info": planner.model_info
                })

            # Handle User Message
            elif msg_type == "user_message":
                try:
                    content = data.get("content", "")
                    planner: PlannerAgent = session["planner"]
                    
                    async def on_step(msg: str):
                        await manager.send_message(websocket, {"type": "thought", "content": msg})
                    
                    response = await planner.process_message(content, on_step=on_step)
                    await manager.send_message(websocket, response)
                except Exception as e:
                    print(f"[IIS] User message error: {e}")
                    await manager.send_message(websocket, {"type": "error", "content": f"Failed to process message: {str(e)}"})

            # Handle Confirmation
            elif msg_type == "confirmation_response":
                try:
                    confirmed = data.get("confirmed", False)
                    values = data.get("values", {})
                    planner: PlannerAgent = session["planner"]
                    
                    async def on_step(msg: str):
                        await manager.send_message(websocket, {"type": "thought", "content": msg})
                        
                    response = await planner.process_message("yes" if confirmed else "no", values=values, on_step=on_step)
                    await manager.send_message(websocket, response)
                except Exception as e:
                    print(f"[IIS] Confirmation error: {e}")
                    await manager.send_message(websocket, {"type": "error", "content": f"Failed to process confirmation: {str(e)}"})

            # Handle Form
            elif msg_type == "form_response":
                try:
                    action = data.get("action")
                    values = data.get("values", {})
                    planner: PlannerAgent = session["planner"]
                    
                    async def on_step(msg: str):
                        await manager.send_message(websocket, {"type": "thought", "content": msg})
                        
                    response = await planner.handle_form_response(action, values, on_step=on_step)
                    await manager.send_message(websocket, response)
                except Exception as e:
                    print(f"[IIS] Form error: {e}")
                    await manager.send_message(websocket, {"type": "error", "content": f"Failed to execute {action}: {str(e)}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[IIS] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await manager.send_message(websocket, {"type": "error", "content": str(e)})
        except:
            pass
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.ws_host, port=config.ws_port, reload=True)
