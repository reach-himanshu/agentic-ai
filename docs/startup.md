# Startup Instructions

Commands to run all three components of the AI Agent UI.

---

## Prerequisites

Ensure you have:
- Node.js 18+ and npm
- Python 3.11+
- Rust (for Tauri)

---

## Start All Services

Open **3 separate terminals**:

### Terminal 1: Backend (FastAPI)
```powershell
cd c:\Users\himanshu.nigam\.gemini\antigravity\scratch\agent-ui\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Orchestrator (AutoGen)
```powershell
cd c:\Users\himanshu.nigam\.gemini\antigravity\scratch\agent-ui\orchestrator
.venv\Scripts\activate
python main.py
```

### Terminal 3: Frontend (Tauri)
```powershell
cd c:\Users\himanshu.nigam\.gemini\antigravity\scratch\agent-ui\frontend
$env:CARGO_HTTP_CHECK_REVOKE = "false"
npx tauri dev
```

---

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Tauri web UI |
| Backend API | http://localhost:8000/docs | FastAPI Swagger docs |
| Orchestrator | ws://localhost:8001 | WebSocket server |

---

## Quick Health Check

```powershell
curl http://localhost:8000/health
```
