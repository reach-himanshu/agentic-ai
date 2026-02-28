import weaviate
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051
    )
    version = client.get_meta()["version"]
    print(f"CLIENT_DETECTED_VERSION={version}")
    print(f"IS_READY={client.is_ready()}")
    client.close()
except Exception as e:
    print(f"CONNECTION_ERROR={str(e)}")
