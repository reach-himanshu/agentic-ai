import asyncio
import json
import websockets
import sys

async def test_ws_protocol():
    uri = "ws://localhost:8001"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # 1. Receive initial system message
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"\n[1] Initial Message: {data}")
            
            # 2. Test Authentication
            print("\n[2] Sending Auth token...")
            await websocket.send(json.dumps({
                "type": "auth",
                "token": "mock-admin-token"
            }))
            
            auth_res = await websocket.recv()
            auth_data = json.loads(auth_res)
            print(f"Auth Response: {auth_data}")
            
            if "content" in auth_data:
                print("✅ Protocol Match: 'content' field found in auth response.")
            else:
                print("❌ Protocol Mismatch: 'content' field NOT found in auth response.")
                print(f"Received keys: {list(auth_data.keys())}")

            # 3. Test General Message
            print("\n[3] Sending 'Hello'...")
            await websocket.send(json.dumps({
                "type": "user_message",
                "content": "Hello, how are you?"
            }))
            
            hello_res = await websocket.recv()
            hello_data = json.loads(hello_res)
            print(f"Assistant Response: {hello_data}")
            
            if "content" in hello_data:
                print("✅ Protocol Match: 'content' field found in assistant response.")
            
            # 4. Test HITL / Confirmation Flow
            print("\n[4] Sending stage update request...")
            await websocket.send(json.dumps({
                "type": "user_message",
                "content": "Update Acme Corp to Qualified stage"
            }))
            
            hitl_res = await websocket.recv()
            hitl_data = json.loads(hitl_res)
            print(f"HITL Response Type: {hitl_data.get('type')}")
            
            if hitl_data.get("type") == "confirmation_request":
                print("✅ Confirmation request received correctly.")
                
                # 5. Test Confirmation with edited values
                print("\n[5] Sending confirmation with custom notes...")
                await websocket.send(json.dumps({
                    "type": "confirmation_response",
                    "confirmed": True,
                    "values": {
                        "notes": "User confirmed via high-priority call."
                    }
                }))
                
                final_res = await websocket.recv()
                final_data = json.loads(final_res)
                print(f"Final Response: {final_data}")
                
                if "content" in final_data and "User confirmed" in final_data["content"]:
                    print("✅ Verification Success: Custom notes were processed by the agent!")
                else:
                    print("❌ Verification Failure: Custom notes might have been ignored.")
            else:
                print("❌ Unexpected response type for stage update.")

    except ConnectionRefusedError:
        print("\n❌ Error: Connection refused. Is the orchestrator running (python main.py)?")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws_protocol())
