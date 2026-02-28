import asyncio
import json
import websockets
import sys

async def test_persona(name, token, should_succeed=True):
    print(f"\n--- Testing Persona: {name} ({token}) ---")
    url = "ws://localhost:8001"
    
    try:
        async with websockets.connect(url) as ws:
            # 1. Wait for Welcome
            welcome = await ws.recv()
            print(f"[{name}] Welcome signal received.")

            # 2. Auth
            await ws.send(json.dumps({"type": "auth", "token": token}))
            auth_res = json.loads(await ws.recv())
            print(f"[{name}] Auth: {auth_res['type']}")
            
            if auth_res["type"] != "auth_success":
                print(f"[FAIL] [{name}] Auth failed")
                return

            # 3. Trigger Plan
            print(f"[{name}] Triggering plan...")
            await ws.send(json.dumps({
                "type": "user_message",
                "content": "Update Acme Corp to Qualified stage"
            }))
            
            # Wait for response
            raw_res = await ws.recv()
            print(f"[{name}] Received: {raw_res}")
            plan_res = json.loads(raw_res)
            print(f"[{name}] Plan Response Type: {plan_res['type']}")
            
            if should_succeed:
                if plan_res["type"] == "confirmation_request":
                    print(f"[OK] [{name}] Correctly received confirmation request.")
                else:
                    print(f"[FAIL] [{name}] Expected confirmation request, got {plan_res['type']}")
                    print(f"   Content: {plan_res.get('content')}")
            else:
                if plan_res["type"] == "error" and "permission" in plan_res["content"].lower():
                    print(f"[OK] [{name}] Correctly blocked with permission error.")
                else:
                    print(f"[FAIL] [{name}] Expected permission error, but got: {plan_res}")

    except Exception as e:
        print(f"[FAIL] [{name}] Connection Error: {e}")

async def main():
    print("Starting Security Verification...")
    
    # 1. Admin - Should Succeed
    try:
        await test_persona("Admin", "mock-admin-token", should_succeed=True)
    except Exception as e:
        print(f"[FAIL] Admin test crashed: {e}")
    await asyncio.sleep(2)
    
    # 2. Sales - Should Succeed
    try:
        await test_persona("Sales", "mock-sales-token", should_succeed=True)
    except Exception as e:
        print(f"[FAIL] Sales test crashed: {e}")
    await asyncio.sleep(2)
    
    # 3. Viewer - Should Fail
    try:
        await test_persona("Viewer", "mock-viewer-token", should_succeed=False)
    except Exception as e:
        print(f"[FAIL] Viewer test crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
