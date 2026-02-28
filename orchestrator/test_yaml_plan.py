import asyncio
import json
import websockets

async def test_yaml_plan_flow():
    uri = "ws://localhost:8001"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # 1. System Welcome
            msg = await websocket.recv()
            print(f"Welcome: {msg}")
            
            # 2. Auth
            print("\nAuthenticating...")
            await websocket.send(json.dumps({"type": "auth", "token": "mock-admin-token"}))
            auth_res = await websocket.recv()
            print(f"Auth Response: {auth_res}")
            
            # 3. Trigger Stage Update (mapped to YAML plan)
            print("\nTriggering stage update plan for Acme Corp...")
            await websocket.send(json.dumps({
                "type": "user_message", 
                "content": "Update Acme Corp to Qualified stage"
            }))
            
            plan_res = await websocket.recv()
            plan_data = json.loads(plan_res)
            print(f"Plan Response: {plan_data}")
            
            if plan_data.get("type") == "confirmation_request":
                print("✅ YAML Plan correctly paused at confirmation step.")
                print(f"Title: {plan_data['confirmation_data']['title']}")
                print(f"Fields: {plan_data['confirmation_data']['fields']}")
                
                # 4. Confirm and Resume
                print("\nConfirming update...")
                await websocket.send(json.dumps({
                    "type": "confirmation_response",
                    "confirmed": True,
                    "values": {"notes": "Verified via YAML flow test."}
                }))
                
                final_res = await websocket.recv()
                print(f"Final Result: {final_res}")
                
                if "Successfully updated" in final_res:
                    print("\n✅ YAML Plan Loader successfully executed!")
                else:
                    print("\n❌ Plan execution failed or returned unexpected message.")
            else:
                print(f"\n❌ Unexpected response type: {plan_data.get('type')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_yaml_plan_flow())
