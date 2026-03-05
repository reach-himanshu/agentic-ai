import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "iis"))
from integrations.knowledge_hub.service import KnowledgeHubClient

async def test_client():
    client = KnowledgeHubClient()
    try:
        results = await client.search("test")
        print("Success:", results)
    except Exception as e:
        print("Error:", str(e))
        print("Type:", type(e))

if __name__ == "__main__":
    asyncio.run(test_client())
