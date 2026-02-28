"""
WebSocket server for real-time communication with frontend.
Uses AutoGen-based agents for processing.
"""
import json
import asyncio
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol

from config import config
from tools.mcp_client import MCPClient
from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent


class WebSocketServer:
    """WebSocket server for frontend communication."""
    
    def __init__(self):
        self.clients: Set[WebSocketServerProtocol] = set()
        self.sessions: dict[WebSocketServerProtocol, dict] = {}
    
    async def register(self, websocket: WebSocketServerProtocol):
        """Register a new client connection."""
        self.clients.add(websocket)
        
        # Create session with AutoGen agents
        mcp_client = MCPClient()
        executor = ExecutorAgent(mcp_client)
        planner = PlannerAgent(executor)
        
        self.sessions[websocket] = {
            "mcp_client": mcp_client,
            "executor": executor,
            "planner": planner,
            "auth_token": None,
        }
        
        print(f"[WS] Client connected. Total: {len(self.clients)}")
    
    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister a client connection."""
        self.clients.discard(websocket)
        
        if websocket in self.sessions:
            session = self.sessions.pop(websocket)
            await session["mcp_client"].close()
        
        print(f"[WS] Client disconnected. Total: {len(self.clients)}")
    
    async def send_message(self, websocket: WebSocketServerProtocol, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def handle_message(
        self, websocket: WebSocketServerProtocol, message: dict
    ) -> dict:
        """Handle incoming message from client."""
        session = self.sessions.get(websocket)
        if not session:
            return {"type": "error", "content": "Session not found"}
        
        msg_type = message.get("type")
        
        # Handle authentication
        if msg_type == "auth":
            token = message.get("token")
            model_id = message.get("model_id")
            auth_flow = message.get("auth_flow", "CLIENT_CREDENTIALS")
            
            session["auth_token"] = token
            session["auth_flow"] = auth_flow
            session["mcp_client"].set_auth_info(token, auth_flow)
            
            # Extract persona info if provided
            user_name = message.get("name")
            user_roles = message.get("roles", [])
            
            # 1. Dynamically fetch tools from backend using the token
            # This list will now be filtered by the backend based on user_roles
            executor: ExecutorAgent = session["executor"]
            await executor.initialize_tools()
            
            # 2. Update planner with auth info and persona context
            planner: PlannerAgent = session["planner"]
            planner.set_auth_info(token, auth_flow)
            if hasattr(planner, "set_persona"):
                planner.set_persona(user_name, user_roles)
            
            # 3. Switch model (re-initializes assistant with the new dynamic tools and persona info)
            if model_id:
                planner.switch_model(model_id)
            else:
                planner.switch_model(planner._active_model.id if planner._active_model else None)
            
            # 4. Trigger initial discovery message
            discovery_res = await planner.process_message("hi")
            
            return {
                "type": "auth_success", 
                "content": discovery_res.get("content", "Authenticated with AutoGen agent"),
                "manifest": discovery_res.get("manifest"),
                "model_info": planner.model_info
            }
        
        # Handle user message
        elif msg_type == "user_message":
            content = message.get("content", "")
            planner = session["planner"]
            
            response = await planner.process_message(content)
            return response
        
        # Handle confirmation response
        elif msg_type == "confirmation_response":
            confirmed = message.get("confirmed", False)
            values = message.get("values", {})
            planner: PlannerAgent = session["planner"]
            
            # Delegate confirmation handling to planner using the same process_message entry point
            response = await planner.process_message("yes" if confirmed else "no", values=values)
            return response
        
        # Handle form response (Actionable UI)
        elif msg_type == "form_response":
            action = message.get("action")
            values = message.get("values", {})
            planner: PlannerAgent = session["planner"]
            
            response = await planner.handle_form_response(action, values)
            return response
        
        return {"type": "error", "content": f"Unknown message type: {msg_type}"}
    
    async def handler(self, websocket: WebSocketServerProtocol):
        """Handle a WebSocket connection."""
        await self.register(websocket)
        
        try:
            await self.send_message(websocket, {
                "type": "system_message",
                "content": "Connected to AI Agent (AutoGen) • Send 'auth' message with token to authenticate",
            })
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.handle_message(websocket, data)
                    await self.send_message(websocket, response)
                except json.JSONDecodeError:
                    await self.send_message(websocket, {"type": "error", "content": "Invalid JSON"})
                except Exception as e:
                    print(f"[WS] Error: {e}")
                    import traceback
                    traceback.print_exc()
                    await self.send_message(websocket, {"type": "error", "content": str(e)})
        
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start the WebSocket server."""
        print(f"[WS] Starting AutoGen WebSocket server on ws://{config.ws_host}:{config.ws_port}")
        
        async with websockets.serve(self.handler, config.ws_host, config.ws_port):
            await asyncio.Future()


ws_server = WebSocketServer()
