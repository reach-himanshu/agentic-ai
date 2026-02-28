import os
import json
import requests
from dotenv import load_dotenv

def deploy_dashboard():
    # Load env from iis/.env
    env_path = os.path.join("iis", ".env")
    load_dotenv(env_path)
    
    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APPLICATION_KEY")
    site = os.getenv("DD_SITE", "datadoghq.com")
    
    if not api_key or not app_key:
        print("Error: DD_API_KEY or DD_APPLICATION_KEY missing from .env")
        return

    # Load dashboard JSON
    dashboard_path = "datadog_agent_insights.json"
    with open(dashboard_path, "r") as f:
        dashboard_data = json.load(f)

    url = f"https://api.{site}/api/v1/dashboard"
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": app_key
    }

    try:
        response = requests.post(url, headers=headers, json=dashboard_data)
        if response.status_code == 200:
            res_json = response.json()
            print(f"SUCCESS: Dashboard created!")
            print(f"ID: {res_json.get('id')}")
            print(f"URL: https://app.{site}/dashboard/{res_json.get('id')}")
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    deploy_dashboard()
