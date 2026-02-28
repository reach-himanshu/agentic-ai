import asyncio
import httpx
import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import SystemMessage, UserMessage

# Security: Configurable SSL verification (default True for security)
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() != "false"

async def test_local_llm():
    print("Testing Local LLM Connectivity...")
    url = "http://127.0.0.1:1234/v1"
    model = "microsoft/phi-4-mini-reasoning"
    
    try:
        # 1. Check if server is up
        async with httpx.AsyncClient(verify=SSL_VERIFY) as client:
            res = await client.get(f"{url}/models")
            print(f"Server Status: {res.status_code}")
            if res.status_code != 200:
                print("❌ LM Studio server not responding correctly.")
                return

        # 2. Test AutoGen Client
        client = OpenAIChatCompletionClient(
            model=model,
            api_key="not-needed",
            base_url=url,
            http_client=httpx.AsyncClient(verify=SSL_VERIFY),
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "family": "gpt-4o",
            }
        )
        
        print(f"Sending message to {model}...")
        response = await client.create(
            messages=[
                SystemMessage(content="You are a helpful assistant."),
                UserMessage(content="Hello, who are you?", source="user")
            ]
        )
        
        print(f"Response: {response.content}")
        print("✅ Local LLM is working!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_local_llm())

