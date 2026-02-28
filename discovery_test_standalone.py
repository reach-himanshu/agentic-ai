import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"
SESSION_ID = f"test-sess-{uuid.uuid4().hex[:8]}"

def test_kb_selection():
    url = f"{BASE_URL}/chat"
    payload = {
        "session_id": SESSION_ID,
        "user_id": "tester",
        "content": "Armanino Knowledge Hub",
        "model_id": "azure-openai",
        "action": "select_area",
        "values": {"value": "kb_hub"}
    }
    
    print(f"Sending selection action: {payload['action']} with value {payload['values']['value']}")
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Agent Response ---")
            print(f"Content: {data.get('content')}")
            manifest = data.get("manifest", {})
            print(f"UI Component: {manifest.get('componentType')}")
            print(f"Payload: {json.dumps(manifest.get('payload'), indent=2)}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_kb_selection()
