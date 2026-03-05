import asyncio
import httpx
import os

async def main():
    try:
        librarian_url = os.environ.get("LIBRARIAN_URL", "http://librarian-gateway:8001")
        print(f"Testing connection to {librarian_url}/health")
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{librarian_url}/health")
            print("Status:", resp.status_code)
            print("Body:", resp.text)
            
        print(f"Testing search endpoint")
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{librarian_url}/api/v1/search?query=test")
            print("Status:", resp.status_code)
            print("Body:", resp.text)
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Type:", type(e))

if __name__ == "__main__":
    asyncio.run(main())
