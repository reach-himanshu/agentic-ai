import asyncio
import httpx

async def test_httpx():
    try:
        async with httpx.AsyncClient() as client:
            await client.get("http://127.0.0.1:9999")
    except Exception as e:
        print("HTTPX Error String:")
        print(f"Error searching knowledge base: {str(e)}")

import weaviate
def test_weaviate():
    try:
        client = weaviate.connect_to_local(port=9999, grpc_port=9998)
    except Exception as e:
        print("Weaviate Error String:")
        print(f"Error searching knowledge base: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_httpx())
    test_weaviate()
