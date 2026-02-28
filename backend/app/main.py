"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

from contextlib import asynccontextmanager
from app.services.mcp_manager import mcp_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to external MCP server (Non-blocking background task)
    await mcp_manager.connect()
    yield
    # Shutdown: Disconnect
    await mcp_manager.disconnect()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for AI Agent UI with MCP protocol support",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API info."""
    return {
        "message": "AI Agent Backend API",
        "docs": "/docs",
        "health": "/health",
    }


# Import and include routers
from app.routers import clients, mcp, plans, models, d365
from app.core.security_azure import get_current_user
from fastapi import Depends

app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients"], dependencies=[Depends(get_current_user)])
app.include_router(d365.router, prefix="/api/v1/d365", tags=["Dynamics 365"], dependencies=[Depends(get_current_user)])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["MCP"], dependencies=[Depends(get_current_user)])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["Plans"], dependencies=[Depends(get_current_user)])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"]) # Models might need to be public for the login screen?
