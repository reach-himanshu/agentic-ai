"""
Agent Orchestrator - Main entry point.
Starts the WebSocket server for frontend communication.
"""
import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ws_server import ws_server


async def main():
    """Main entry point."""
    print("=" * 60)
    print("  AI Agent Orchestrator")
    print("=" * 60)
    print()
    print("Starting services...")
    print()
    
    # Start WebSocket server
    await ws_server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
