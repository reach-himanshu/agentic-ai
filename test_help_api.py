import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"
SESSION_ID = f"debug-help-{uuid.uuid4().hex[:8]}"

def test_help_trigger():
    url = f"{BASE_URL}/chat"
    payload = {
        "session_id": SESSION_ID,
        "user_id": "tester",
        "content": "help",
        "model_id": "azure-openai"
    }
    
    print(f"Sending message: '{payload['content']}'")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
        except Exception:
            print(f"Raw Response: {response.text}")
            return

        if response.status_code == 200:
            print("\n--- Agent Response ---")
            if isinstance(data, dict):
                print(f"Content: {data.get('content')}")
                manifest = data.get("manifest", {})
                if manifest:
                    print(f"UI Component: {manifest.get('componentType')}")
                    print(f"Payload Labels: {[p.get('label') for p in manifest.get('payload', [])]}")
                else:
                    print("No manifest returned.")
            else:
                print(f"Response data is not a dict: {data}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_help_trigger()
