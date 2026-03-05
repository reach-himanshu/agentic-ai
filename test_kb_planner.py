import asyncio
import os
import sys

# Add the iis directory to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "iis"))

from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent
from core.database import init_db

async def test_planner():
    await init_db()
    executor = ExecutorAgent(None)
    await executor.initialize_tools()
    
    planner = PlannerAgent(executor)
    # Simulate a query from the knowledge hub pill
    planner.active_area = "knowledge_hub"
    
    # Mocking sync context and setting required attributes
    planner._user_roles = ["OpsIQ.User"]
    
    # This simulates what happens when process_message gets an 'ask' action with areaId='knowledge_hub'
    user_query = "What is our expense policy?"
    
    print(f"Testing query: {user_query}")
    
    async def on_step(msg):
        print(f"STEP: {msg}")
        
    try:
        response = await planner.process_message(user_query, on_step=on_step)
        print("RESPONSE STATUS:", response.get("type"))
        print("RESPONSE CONTENT:", response.get("content"))
        if response.get("manifest"):
            print("MANIFEST:", response.get("manifest"))
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_planner())
