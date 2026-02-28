from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import weaviate
from weaviate.classes.config import Property, DataType, Configure
import os
import io
import uvicorn
from typing import List, Optional
from pypdf import PdfReader
from docx import Document as DocxDocument
import re
import httpx

app = FastAPI(title="Ops IQ Librarian Gateway")

# Static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Favicon route
@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(STATIC_DIR, "favicon.png")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")

print(f"[DEBUG] weaviate-client version: {weaviate.__version__}")

# Weaviate Client Setup
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://127.0.0.1:8080")
host_parts = WEAVIATE_URL.split("//")[1].split(":")
target_host = host_parts[0]
if target_host == "localhost":
    target_host = "127.0.0.1"

print(f"[DEBUG] Connecting to host: {target_host}")
client = weaviate.connect_to_local(
    host=target_host,
    port=8080,
    grpc_port=50051
)

if not client.is_ready():
    import time
    time.sleep(2)
    print("[DEBUG] Retrying Weaviate connection...")
    client = weaviate.connect_to_local(host=target_host, port=8080, grpc_port=50051)

print(f"[DEBUG] Client is_ready: {client.is_ready()}")

# Initialize Collection Schema
def init_schema():
    try:
        if not client.collections.exists("EnterpriseKnowledge"):
            print("[Librarian] Creating 'EnterpriseKnowledge' collection with Local Transformers...")
            client.collections.create(
                name="EnterpriseKnowledge",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="domain", data_type=DataType.TEXT, index_searchable=True),
                    Property(name="partition", data_type=DataType.TEXT, index_searchable=True),
                    Property(name="source_name", data_type=DataType.TEXT),
                    Property(name="chunk_index", data_type=DataType.INT),
                    Property(name="is_deleted", data_type=DataType.BOOL),
                ]
            )
            print("[Librarian] Collection created.")
        else:
            print("[Librarian] 'EnterpriseKnowledge' collection exists. Checking properties...")
            collection = client.collections.get("EnterpriseKnowledge")
            config = collection.config.get()
            if not any(p.name == "is_deleted" for p in config.properties):
                print("[Librarian] Adding 'is_deleted' property...")
                collection.config.add_property(Property(name="is_deleted", data_type=DataType.BOOL))
    except Exception as e:
        print(f"[Librarian] Schema init error: {e}")

async def backfill_is_deleted():
    """Ensure all existing objects have is_deleted set to False if it's missing/null."""
    print("[Librarian] Checking for documents with missing 'is_deleted' status...")
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        # Fetch all objects and check manually if we can't filter by is_none
        response = collection.query.fetch_objects(
            limit=10000,
            return_properties=["is_deleted", "source_name"]
        )
        
        objects_to_update = []
        for obj in response.objects:
            if obj.properties.get("is_deleted") is None:
                objects_to_update.append(obj.uuid)
        
        if objects_to_update:
            print(f"[Librarian] Backfilling {len(objects_to_update)} objects...")
            for uuid in objects_to_update:
                collection.data.update(
                    uuid=uuid,
                    properties={"is_deleted": False}
                )
            print("[Librarian] Backfill complete.")
        else:
            print("[Librarian] No backfill needed.")
    except Exception as e:
        print(f"[Librarian] Backfill error: {e}")

@app.on_event("startup")
async def startup():
    print("[Librarian] Starting up...")
    init_schema()

# Helpers
def extract_text(file_content: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_content))
        return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif filename.lower().endswith(".docx"):
        doc = DocxDocument(io.BytesIO(file_content))
        return " ".join([p.text for p in doc.paragraphs])
    else:
        return file_content.decode("utf-8", errors="ignore")

def chunk_text(text: str, chunk_size=1000, overlap=100) -> List[str]:
    words = re.findall(r'\S+\s*', text)
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        current_chunk.append(word)
        current_length += len(word)
        if current_length >= chunk_size:
            chunks.append("".join(current_chunk))
            overlap_words = current_chunk[-max(1, int(len(current_chunk)*0.1)):] 
            current_chunk = overlap_words
            current_length = len("".join(current_chunk))
    if current_chunk:
        chunks.append("".join(current_chunk))
    return chunks

# --- API ROUTES (Defined FIRST for correct precedence) ---

@app.get("/health")
async def health():
    return {"status": "ok", "weaviate_connected": client.is_ready()}

@app.get("/api/v1/meta")
async def meta():
    return {
        "name": "Ops IQ Librarian Gateway",
        "status": "online",
        "endpoints": ["/health", "/search", "/ingest/file", "/ingest/url", "/api/v1/documents"]
    }

@app.get("/api/v1/documents")
async def list_documents():
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        # Aggregating unique source_names using grouping
        # In Weaviate v4, we use groupby to get distinct properties
        response = collection.query.fetch_objects(
            limit=1000,
            return_properties=["source_name", "domain", "is_deleted", "partition"]
        )
        
        docs = {}
        for obj in response.objects:
            name = obj.properties.get("source_name")
            if name and name not in docs:
                is_deleted = obj.properties.get("is_deleted", False)
                if is_deleted is None: is_deleted = False # Extra safety
                docs[name] = {
                    "source_name": name,
                    "domain": obj.properties.get("domain"),
                    "partition": obj.properties.get("partition"),
                    "is_deleted": is_deleted,
                    "is_active": not is_deleted
                }
        return list(docs.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/meta/domains")
async def list_domains():
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        response = collection.query.fetch_objects(
            limit=10000,
            return_properties=["domain"]
        )
        domains = set()
        for obj in response.objects:
            d = obj.properties.get("domain")
            if d: domains.add(d)
        return sorted(list(domains))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/meta/partitions")
async def list_partitions():
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        response = collection.query.fetch_objects(
            limit=10000,
            return_properties=["partition"]
        )
        partitions = set()
        for obj in response.objects:
            p = obj.properties.get("partition")
            if p: partitions.add(p)
        return sorted(list(partitions))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MetadataUpdate(BaseModel):
    domain: Optional[str] = None
    partition: Optional[str] = None

@app.patch("/api/v1/documents/{source_name}/metadata")
async def update_document_metadata(source_name: str, update: MetadataUpdate):
    print(f"[Librarian] Metadata update request for: {source_name}")
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        # Fetch all objects for this source_name to get their UUIDs
        response = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("source_name").equal(source_name),
            limit=10000
        )
        
        if not response.objects:
            return {"message": f"No objects found for {source_name}", "updated": 0}

        update_data = {}
        if update.domain is not None: update_data["domain"] = update.domain
        if update.partition is not None: update_data["partition"] = update.partition

        if not update_data:
            return {"message": "No metadata changes provided.", "updated": 0}

        print(f"[Librarian] Updating metadata for {len(response.objects)} chunks...")
        for obj in response.objects:
            collection.data.update(
                uuid=obj.uuid,
                properties=update_data
            )
        
        return {"message": f"Document {source_name} metadata updated.", "updated": len(response.objects)}
    except Exception as e:
        print(f"[Librarian] Metadata update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/documents/{source_name}/deactivate")
async def deactivate_document(source_name: str):
    print(f"[Librarian] Deactivate request for: {source_name}")
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        # Fetch all objects for this source_name to get their UUIDs
        response = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("source_name").equal(source_name),
            limit=10000
        )
        
        if not response.objects:
            return {"message": f"No objects found for {source_name}", "updated": 0}

        print(f"[Librarian] Deactivating {len(response.objects)} chunks...")
        for obj in response.objects:
            collection.data.update(
                uuid=obj.uuid,
                properties={"is_deleted": True}
            )
        
        return {"message": f"Document {source_name} deactivated.", "updated": len(response.objects)}
    except Exception as e:
        print(f"[Librarian] Deactivate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/documents/{source_name}/activate")
async def activate_document(source_name: str):
    print(f"[Librarian] Activate request for: {source_name}")
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        response = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("source_name").equal(source_name),
            limit=10000
        )
        if not response.objects:
            return {"message": f"No objects found for {source_name}", "updated": 0}
        print(f"[Librarian] Activating {len(response.objects)} chunks...")
        for obj in response.objects:
            collection.data.update(uuid=obj.uuid, properties={"is_deleted": False})
        return {"message": f"Document {source_name} activated.", "updated": len(response.objects)}
    except Exception as e:
        print(f"[Librarian] Activate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents/{source_name}/content")
async def get_document_content(source_name: str):
    """Retrieve the full consolidated text of a document by joining all its chunks."""
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        response = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("source_name").equal(source_name),
            return_properties=["content", "chunk_index"],
            limit=10000
        )
        
        if not response.objects:
            raise HTTPException(status_code=404, detail=f"Document '{source_name}' not found.")
            
        # Sort by chunk_index to ensure correct order
        sorted_chunks = sorted(response.objects, key=lambda x: x.properties.get("chunk_index", 0))
        full_text = "\n".join([str(obj.properties.get("content", "")) for obj in sorted_chunks])
        
        return {
            "source_name": source_name,
            "chunk_count": len(sorted_chunks),
            "content": full_text
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Librarian] Error fetching document content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/documents/{source_name}")
async def delete_document(source_name: str):
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        collection.data.delete_many(
            where=weaviate.classes.query.Filter.by_property("source_name").equal(source_name)
        )
        return {"message": f"Document {source_name} permanently deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    domain: str = "general",
    partition: str = "knowledge"
):
    try:
        content = await file.read()
        raw_text = extract_text(content, file.filename)
        chunks = chunk_text(raw_text)
        collection = client.collections.get("EnterpriseKnowledge")
        with collection.batch.dynamic() as batch:
            for i, chunk in enumerate(chunks):
                batch.add_object({
                    "content": chunk,
                    "domain": domain,
                    "partition": partition,
                    "source_name": file.filename,
                    "chunk_index": i,
                    "is_deleted": False
                })
        if collection.batch.failed_objects:
            raise HTTPException(status_code=500, detail="Partial ingestion failure.")
        return {"message": f"Successfully ingested {file.filename}", "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/url")
async def ingest_url(url: str, domain: str = "web"):
    """
    Ingest content from a URL with comprehensive SSRF protection.
    Uses IP pinning to prevent DNS rebinding attacks.
    """
    from urllib.parse import urlparse
    import ipaddress
    import socket
    
    parsed = urlparse(url)
    
    # 1. Validate scheme - only allow http/https
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed")
    
    # 2. Require hostname
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: hostname required")
    
    # 3. Block known internal hostnames
    blocked_hosts = [
        "localhost", "127.0.0.1", "0.0.0.0", "::1", 
        "metadata", "metadata.google.internal",
        "169.254.169.254",  # AWS/GCP/Azure metadata endpoint
        "fd00:ec2::254",    # AWS IMDSv2 IPv6
    ]
    hostname_lower = parsed.hostname.lower()
    if hostname_lower in blocked_hosts or hostname_lower.endswith(".internal"):
        raise HTTPException(status_code=400, detail="Internal URLs are not allowed")
    
    # 4. Resolve hostname to IP and validate BEFORE making request
    try:
        resolved_ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
        
        # Block private, loopback, link-local, and reserved IPs
        if (ip_obj.is_private or 
            ip_obj.is_loopback or 
            ip_obj.is_link_local or 
            ip_obj.is_reserved or
            ip_obj.is_multicast):
            raise HTTPException(
                status_code=400, 
                detail=f"URL resolves to blocked IP range: {resolved_ip}"
            )
        
        # Specifically block cloud metadata IP ranges
        metadata_ranges = [
            ipaddress.ip_network("169.254.0.0/16"),  # Link-local / metadata
            ipaddress.ip_network("100.64.0.0/10"),   # Carrier-grade NAT
        ]
        for net in metadata_ranges:
            if ip_obj in net:
                raise HTTPException(
                    status_code=400, 
                    detail="URL resolves to blocked metadata IP range"
                )
                
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Unable to resolve hostname")
    
    # 5. Make request with IP pinning to prevent DNS rebinding
    # Pin the resolved IP so the actual request uses the validated IP
    try:
        # Create a transport that pins to the resolved IP
        import httpx
        
        # Build the URL with the resolved IP instead of hostname
        # Preserve the Host header for proper routing
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        pinned_url = f"{parsed.scheme}://{resolved_ip}:{port}{parsed.path}"
        if parsed.query:
            pinned_url += f"?{parsed.query}"
        
        async with httpx.AsyncClient(verify=True, timeout=30.0) as h_client:
            res = await h_client.get(
                pinned_url,
                headers={"Host": parsed.hostname},  # Preserve original Host header
                follow_redirects=False  # Don't follow redirects to prevent redirect-based SSRF
            )
            
            # If redirect, validate the redirect URL too
            if res.is_redirect:
                raise HTTPException(
                    status_code=400, 
                    detail="URL redirects are not allowed for security reasons"
                )
            
            text = re.sub('<[^<]+?>', '', res.text)
            chunks = chunk_text(text)
            collection = client.collections.get("EnterpriseKnowledge")
            with collection.batch.dynamic() as batch:
                for i, chunk in enumerate(chunks):
                    batch.add_object({
                        "content": chunk, "domain": domain, "partition": "web", "source_name": url, "chunk_index": i, "is_deleted": False
                    })
            return {"message": f"Ingested URL: {url}", "chunks": len(chunks)}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/search")
async def search(query: str, domain: Optional[str] = None):
    try:
        collection = client.collections.get("EnterpriseKnowledge")
        # Filter for active documents only
        base_filter = weaviate.classes.query.Filter.by_property("is_deleted").equal(False)
        if domain:
            base_filter = base_filter & weaviate.classes.query.Filter.by_property("domain").equal(domain)
            
        response = collection.query.hybrid(
            query=query,
            filters=base_filter,
            limit=5,
            return_metadata=weaviate.classes.query.MetadataQuery(score=True)
        )
        results = []
        for obj in response.objects:
            results.append({
                "content": obj.properties["content"],
                "metadata": {
                    "source": obj.properties["source_name"],
                    "domain": obj.properties["domain"],
                    "score": obj.metadata.score if obj.metadata else 0
                }
            })
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- SPA & STATIC ROUTES (Defined LAST) ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIST_PATH = os.path.join(BASE_DIR, "..", "knowledge-hub-ui", "dist")

@app.get("/")
async def root():
    index_path = os.path.join(UI_DIST_PATH, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Knowledge Hub UI not built."}

if os.path.exists(UI_DIST_PATH):
    app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_PATH, "assets")), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Security: Normalize and validate path to prevent path traversal
    # Ensure the resolved path stays within UI_DIST_PATH
    base_path = os.path.abspath(UI_DIST_PATH)
    requested_path = os.path.normpath(os.path.join(UI_DIST_PATH, full_path))
    
    # Prevent path traversal attacks
    if not requested_path.startswith(base_path):
        return {"error": "Invalid path"}
    
    if os.path.exists(requested_path) and os.path.isfile(requested_path):
        return FileResponse(requested_path)
    index_path = os.path.join(UI_DIST_PATH, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Not Found"}

if __name__ == "__main__":
    print("[Librarian] Entry point reached. Starting uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
