"""
Simple test script to verify Azure OpenAI connectivity and agent logic.
"""
import asyncio
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent
from tools.mcp_client import MCPClient

async def test_llm_connection():
    print("Checking configuration...")
    llm_config = config.get_llm_config()
    print(f"Model: {config.azure_openai_model_name}")
    print(f"Endpoint: {config.azure_openai_endpoint}")
    
    if not config.azure_openai_api_key:
        print("❌ Error: AZURE_OPENAI_API_KEY not found in .env")
        return

    print("\nInitializing agents...")
    mcp_client = MCPClient(config.backend_url)
    executor = ExecutorAgent(mcp_client)
    planner = PlannerAgent(executor)
    
    print("\nSending test message: 'Hello, what can you do?'")
    try:
        response = await planner.process_message("Hello, what can you do?")
        if response.get("type") == "error":
             print(f"\n❌ Error from Agent: {response.get('content')}")
        else:
            print(f"\nAssistant Response: {response.get('content')}")
            print("\n✅ Azure OpenAI integration verified!")
    except Exception as e:
        import traceback
        print(f"\n❌ Exception during test: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_connection())
