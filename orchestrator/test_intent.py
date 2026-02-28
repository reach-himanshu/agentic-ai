import asyncio
import json
import websockets

async def test_intent(query, expected_client, expected_stage):
    print(f"\n--- Testing Query: '{query}' ---")
    url = "ws://localhost:8001"
    token = "mock-admin-token"
    
    try:
        async with websockets.connect(url) as ws:
            # 1. Auth
            await ws.recv()
            await ws.send(json.dumps({"type": "auth", "token": token}))
            await ws.recv()

            # 2. Send Message
            await ws.send(json.dumps({
                "type": "user_message",
                "content": query
            }))
            
            # Wait for response
            raw_res = await ws.recv()
            res = json.loads(raw_res)
            
            if res["type"] == "confirmation_request":
                data = res["confirmation_data"]
                fields = {f["key"]: f["value"] for f in data["fields"]}
                new_stage_field = next((f["newValue"] for f in data["fields"] if f["key"] == "currentStage"), None)
                
                client_name = fields.get("clientName", "")
                
                print(f"[Result] Client: {client_name}, New Stage: {new_stage_field}")
                
                if expected_client.lower() in client_name.lower() and expected_stage.lower() == new_stage_field.lower():
                    print(f"✅ [OK] Successfully detected intent and extracted parameters.")
                else:
                    print(f"❌ [FAIL] Parameter mismatch. Expected {expected_client}/{expected_stage}")
            else:
                print(f"❌ [FAIL] Expected confirmation_request, but got {res['type']}")
                print(f"   Content: {res.get('content')}")

    except Exception as e:
        print(f"❌ [FAIL] Error: {e}")

async def main():
    # Test 1: Global Tech to Negotiation (Valid: qualified -> negotiation)
    await test_intent("Can you move Global Tech to the negotiation stage?", "Global Tech", "negotiation")
    
    await asyncio.sleep(2)
    
    # Test 2: Acme to Qualified (Valid: prospect -> qualified)
    await test_intent("Mark Acme Corp as qualified", "Acme Corporation", "qualified")

if __name__ == "__main__":
    asyncio.run(main())
