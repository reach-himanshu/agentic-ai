# Ops IQ Multi-Platform Deployment Strategy

## Architecture Overview

**Current Stack:**
- **Frontend**: React/Vite (shared codebase)
- **Desktop**: Tauri wrapper
- **Web**: Direct Vite build
- **Mobile**: Tauri Mobile (iOS/Android)
- **Backend**: IIS (FastAPI) + Librarian Gateway + PostgreSQL + Weaviate
- **Auth**: Entra ID + Workday PKCE

---

## Multi-Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SHARED REACT CODEBASE                        │
│                   (frontend/src/*)                               │
├─────────────────────────────────────────────────────────────────┤
│  Components │ Pages │ Hooks │ Context │ Services │ Styles       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┬─────────────────┐
       ▼                   ▼                   ▼                 ▼
 ┌───────────┐      ┌───────────┐      ┌───────────────┐  ┌───────────┐
 │  TAURI    │      │   WEB     │      │   MOBILE      │  │  MS TEAMS │
 │  Desktop  │      │  Browser  │      │ iOS / Android │  │ Personal  │
 └───────────┘      └───────────┘      └───────────────┘  │   Tab     │
                                                          └───────────┘
```

### Build Commands

| Platform | Command | Output |
|----------|---------|--------|
| Desktop | `npm run tauri build` | MSI/DMG installer |
| Web | `npm run build` | dist/ static files |
| Android | `npm run tauri android build` | APK/AAB |
| iOS | `npm run tauri ios build` | IPA |
| Teams | `npm run build:teams` | dist/ + manifest.zip |

---

## OAuth Redirect URIs

### Azure Entra ID App Registration

```
Type: Public client/native (mobile & desktop)

Redirect URIs:
  - opsiq://auth/callback           (Desktop + Mobile)
  - https://app.opsiq.armanino.com/auth/callback  (Web)
  - https://app.opsiq.armanino.com/auth/teams-end  (Teams SSO)
  - http://localhost                (Development)
```

### Workday API Client (PKCE Enabled)

```
Client Grant Type:     Authorization Code Grant
PKCE Support:          ✅ Enabled (required for custom schemes)
Access Token Type:     Bearer

Redirection URIs:
  - opsiq://workday/callback
  - https://app.opsiq.armanino.com/workday/callback

Allowed Origins (CORS):
  - https://api.opsiq.armanino.com
```

> **Note**: Custom protocol schemes (`opsiq://`) only work with PKCE enabled in Workday.

---

## MS Teams Integration (Personal Tab)

### Architecture

```
┌─────────────────────────────────────────┐
│ Teams Left Rail                         │
│ ┌─────┐                                 │
│ │ 💬 │ Chat                             │
│ │ 👥 │ Teams                            │
│ │ 📅 │ Calendar                         │
│ │ ⭐ │ Ops IQ  ← Personal Tab           │
│ └─────┘                                 │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  React App (iFrame in Teams)            │
│  - Teams SDK for silent SSO             │
│  - Full GenUI capabilities              │
│  - Same codebase as Web                 │
└─────────────────────────────────────────┘
```

### Teams Manifest (`manifest.json`)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "id": "{{APP_ID}}",
  "version": "1.0.0",
  "name": { "short": "Ops IQ", "full": "Ops IQ AI Assistant" },
  "description": {
    "short": "AI-powered operations assistant",
    "full": "Unified access to D365, Workday, ServiceNow, M365, and Knowledge Hub"
  },
  "developer": {
    "name": "Armanino",
    "websiteUrl": "https://armanino.com",
    "privacyUrl": "https://app.opsiq.armanino.com/privacy",
    "termsOfUseUrl": "https://app.opsiq.armanino.com/terms"
  },
  "staticTabs": [
    {
      "entityId": "opsiq",
      "name": "Ops IQ",
      "contentUrl": "https://app.opsiq.armanino.com/teams",
      "scopes": ["personal"]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["app.opsiq.armanino.com", "api.opsiq.armanino.com"]
}
```

### Teams SSO Flow

```typescript
// src/utils/teamsAuth.ts
import * as microsoftTeams from "@microsoft/teams-js";

export async function getTeamsToken(): Promise<string> {
  await microsoftTeams.app.initialize();
  
  const token = await microsoftTeams.authentication.getAuthToken();
  // Token is an ID token from Teams, exchange it via OBO on backend
  return token;
}

// Backend exchanges Teams token for downstream tokens (D365, Graph, etc.)
```

### Platform Detection Update

```typescript
// src/utils/platform.ts
export const getPlatform = () => {
  if (window.microsoftTeams) return 'teams';  // NEW
  if (window.__TAURI__) return 'tauri';
  if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) return 'mobile';
  return 'web';
};
```

### Deployment Options

| Stage | Method | Admin Required |
|-------|--------|----------------|
| POC/Demo | Sideload (.zip) | ❌ No (if enabled) |
| Pilot | IT uploads to group | Maybe |
| Firm-wide | Teams Admin Center | ✅ Yes |

### Sideloading Steps

1. Create `manifest.json` + `color.png` (192x192) + `outline.png` (32x32)
2. Zip all three files
3. Teams → Apps → "Upload a custom app"
4. App appears in left sidebar

---

## Phase 1: Pilot Distribution (10-50 users)

### Distribution Options

| Method | Platform | Recommended For |
|--------|----------|-----------------|
| SharePoint/MSI | Desktop | Internal pilot |
| Azure Static Web Apps | Web | Browser users |
| TestFlight/Internal Testing | Mobile | Mobile pilot |

### Pilot Architecture

```
Users (10-50)
    ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Desktop    │  │  Web        │  │  Mobile     │
│  (Tauri)    │  │  (Browser)  │  │  (Tauri)    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Azure Container │
              │ Apps (Backend)  │
              └────────┬────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
     Azure PG Flex          Azure AI Search
```

---

## Phase 2: Production (1000+ Users)

### Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Desktop/Web/Mobile Clients                                      │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────────────┐
        │   Azure Front Door (CDN + WAF + LB)       │
        └────────────────────┬─────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
   Azure Static                      Azure Container Apps
   Web Apps (Web)                    (API Backend)
                                     ┌──────────────────┐
                                     │ IIS + Librarian  │
                                     │ (3-10 replicas)  │
                                     └────────┬─────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                       Azure PG Flex                   Azure AI Search
                       (HA, Read Replicas)
```

### Scaling by Platform

| Component | Pilot | Production |
|-----------|-------|------------|
| Desktop Distribution | SharePoint | Tauri Updater + Azure Blob |
| Web Hosting | Azure Static Web Apps | Front Door + CDN |
| Mobile Distribution | TestFlight/Internal | App Store / Play Store |
| Backend | 1 Container | 3-10 replicas (auto-scale) |
| Database | PG Flex Basic | PG Flex GP (HA) |

---

## Auto-Update Configuration

### Tauri Updater (`tauri.conf.json`)

```json
{
  "plugins": {
    "updater": {
      "endpoints": ["https://releases.opsiq.armanino.com/latest.json"],
      "pubkey": "YOUR_PUBLIC_KEY"
    }
  }
}
```

### Update Manifest (`latest.json`)

```json
{
  "version": "1.0.0",
  "platforms": {
    "windows-x86_64": {
      "signature": "...",
      "url": "https://releases.opsiq.armanino.com/Ops_IQ_1.0.0_x64.msi.zip"
    },
    "darwin-aarch64": {
      "signature": "...",
      "url": "https://releases.opsiq.armanino.com/Ops_IQ_1.0.0_aarch64.app.tar.gz"
    }
  }
}
```

---

## Cost Estimates (Monthly)

| Component | Pilot (50 users) | Production (1000 users) |
|-----------|------------------|-------------------------|
| Azure Container Apps | ~$50 | ~$300-500 |
| Azure PG Flexible | ~$50 | ~$200 |
| Azure Static Web Apps | ~$10 | ~$20 |
| Azure Blob (releases) | ~$5 | ~$20 |
| Azure Front Door | - | ~$100 |
| Azure AI Search | - | ~$250 |
| **Total** | **~$115/mo** | **~$890-1090/mo** |

---

## Platform Detection (Frontend)

```typescript
// src/utils/platform.ts
export const getPlatform = () => {
  if (window.__TAURI__) return 'tauri';
  if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) return 'mobile';
  return 'web';
};

export const getAuthRedirectUri = () => {
  const platform = getPlatform();
  switch (platform) {
    case 'tauri':
    case 'mobile':
      return 'opsiq://auth/callback';
    case 'web':
    default:
      return 'https://app.opsiq.armanino.com/auth/callback';
  }
};
```

---

## Knowledge Hub Caching Strategy

### Caching Priority (Recommended)

| Priority | Cache Layer | Size Impact | Value | Cache? |
|----------|-------------|-------------|-------|--------|
| **1st** | Embedding Cache | ~50 MB | High (API cost savings) | ✅ Yes |
| **2nd** | Semantic Response Cache | ~100 MB | Very High (cost + latency) | ✅ Yes |
| **3rd** | Search Result Cache | ~50 MB | Medium (latency) | ✅ Yes |
| ~~4th~~ | ~~Document Chunks~~ | ~~500 MB+~~ | ~~Low~~ | ❌ Skip |

> **Why skip chunk caching?** Vector DBs (Weaviate/Azure AI Search) already cache hot data in memory. Chunk caching consumes 5-10x more space with diminishing returns.

### Cache Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: SEMANTIC CACHE (LLM Response)                          │
│  Key: semantic_hash(query)  |  TTL: 7 days  |  Hit: 30-60%       │
│  ✅ HIT → Return cached response immediately                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MISS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: EMBEDDING CACHE                                        │
│  Key: hash(query_text)  |  TTL: 30 days  |  Hit: 50-80%          │
│  ✅ HIT → Skip embedding API call                                │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MISS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: SEARCH RESULT CACHE                                    │
│  Key: hash(embedding + filters)  |  TTL: 4h  |  Hit: 40-70%      │
│  ✅ HIT → Skip vector similarity search                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MISS
                              ▼
                    Vector DB → LLM Generation
```

### Implementation (Redis)

```python
class KnowledgeHubCache:
    def __init__(self, redis: Redis, max_memory_mb: int = 256):
        self.redis = redis
        redis.config_set("maxmemory", f"{max_memory_mb}mb")
        redis.config_set("maxmemory-policy", "allkeys-lru")
    
    # Embedding cache
    async def get_embedding(self, text: str) -> list[float] | None:
        return self.redis.get(f"emb:{hash(text)}")
    
    # Semantic response cache (similarity > 0.95)
    async def get_similar_response(self, query_embedding: list[float]) -> dict | None:
        # Find cached query with cosine similarity > 0.95
        ...
```

### Cache Invalidation

```python
async def on_document_update(document_id: str):
    """Invalidate caches when corpus changes."""
    # Invalidate search results (may be stale)
    redis.delete(*redis.keys("search:*"))
    # Bump corpus version for lazy invalidation
    redis.set("corpus_version", str(uuid.uuid4()))
```

### Azure Cache for Redis Sizing

| Scale | Cache Size | Cost/Month |
|-------|------------|------------|
| Pilot (50 users) | Basic 250MB | ~$16 |
| Production (1000) | Standard 1GB | ~$50 |

### Cost Savings Estimate (1000 users)

| Metric | Without Cache | With Cache | Savings |
|--------|---------------|------------|---------|
| Embedding API calls | 50K/day | 15K/day | ~$35/mo |
| LLM API calls | 50K/day | 25K/day | ~$500/mo |
| **Total API Savings** | - | - | **~$535/mo** |

---

## Web App vs Native App Trade-offs

### Comparison Matrix

| Aspect | Web App | Native App (Tauri) | Winner |
|--------|---------|-------------------|--------|
| Deployment Cost | ~$10-50/mo | $0 (client-side) | 🏆 Native |
| Deployment Slots | ✅ Built-in | ❌ Not available | 🏆 Web |
| Feature Flags | ✅ Easy | ⚠️ Backend-driven | 🏆 Web |
| Instant Rollback | ✅ Slot swap | ⚠️ User must update | 🏆 Web |
| Offline Capability | ❌ Limited | ✅ Full | 🏆 Native |
| OS Integration | ❌ Limited | ✅ Full | 🏆 Native |
| App Store Presence | ❌ N/A | ✅ Professional | 🏆 Native |

### Mitigating Native App Cons

| Native App Con | Mitigation Strategy |
|----------------|---------------------|
| No deployment slots | Backend-driven UI config via `/api/v1/config` |
| No feature flags | Backend API or LaunchDarkly integration |
| No instant rollback | Staged rollouts + version kill switch |
| No A/B testing | User cohorts + analytics tracking |
| Slow update adoption | Forced update API + Tauri auto-updater |

### Feature Flags via Backend

```typescript
// Frontend fetches feature config from backend
const config = await fetch('/api/v1/features?user_id=xxx');
// { "newChatUI": true, "betaFeatures": false }
```

### Version Control API

```python
@app.get("/api/v1/version-check")
async def check_version(client_version: str):
    if client_version in BLOCKED_VERSIONS:
        return {"status": "blocked", "message": "Critical issue..."}
    if client_version < MIN_VERSION:
        return {"status": "update_required", "url": "..."}
    return {"status": "ok", "features": {...}}
```

---

## Container Orchestration

### Load Balancing (Automatic in Azure Container Apps)

```
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE CONTAINER APPS                          │
├─────────────────────────────────────────────────────────────────┤
│   INGRESS (Built-in Load Balancer)                              │
│   • Round-robin distribution                                     │
│   • Health checks (removes unhealthy pods)                       │
│   • HTTPS termination                                            │
│                               │                                  │
│    Request 1 ─────────────────┼──────────────→ Pod #1           │
│    Request 2 ─────────────────┼──────────────→ Pod #2           │
│    Request 3 ─────────────────┼──────────────→ Pod #3           │
└───────────────────────────────┴──────────────────────────────────┘
```

### Auto-Scaling Configuration

```yaml
# containerapp.yaml
properties:
  template:
    scale:
      minReplicas: 2          # High availability
      maxReplicas: 10         # Handle spikes
      rules:
        - name: http-scaling
          http:
            metadata:
              concurrentRequests: 50   # Scale if > 50 req/pod
```

### Scaling Timeline Example

| Time | Requests | Pods | What Happens |
|------|----------|------|--------------|
| 9:00 AM | 10/min | 2 | Normal (minReplicas) |
| 10:00 AM | 200/min | 4 | Scaled up |
| 12:00 PM | 500/min | 10 | At max capacity |
| 6:00 PM | 50/min | 2 | Scaled down |

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
```

---

## Critical Deployment Considerations

### Deployment Readiness Checklist

| Category | Item | Priority |
|----------|------|----------|
| **Database** | Migration strategy (expand/contract) | 🔴 Critical |
| **Secrets** | Azure Key Vault integration | 🔴 Critical |
| **CI/CD** | Automated build/test/deploy | 🟠 Important |
| **Deployment** | Blue/Green or Canary releases | 🟠 Important |
| **API** | Version strategy (/v1, /v2) | 🟠 Important |
| **Observability** | Correlation IDs + centralized logs | 🟡 Needed |
| **Security** | Rate limiting | 🟡 Needed |

### 1. Database Migrations (Expand/Contract Pattern)

```
SAFE MIGRATION STRATEGY
─────────────────────────────────────────
PHASE 1: EXPAND
  - Add new column (nullable)
  - Deploy code that writes to BOTH columns
  - Old and new pods coexist safely

PHASE 2: MIGRATE
  - Backfill existing rows

PHASE 3: CONTRACT
  - Deploy code using only new column
  - Drop old column
```

### 2. Secrets Management (Azure Key Vault)

```yaml
# containerapp.yaml - reference secrets from Key Vault
properties:
  configuration:
    secrets:
      - name: db-connection
        keyVaultUrl: https://opsiq-vault.vault.azure.net/secrets/database-url
        identity: system
```

### 3. Blue/Green Deployment

```
STEP 1: Deploy v2.0 to Green (100% → Blue)
STEP 2: Test Green internally
STEP 3: Swap traffic (100% → Green)
STEP 4: Keep Blue as rollback
```

**Azure Traffic Splitting**:
```bash
# Canary: 10% to new version
az containerapp ingress traffic set \
  --revision-weight v1=90 v2=10

# Full rollout
az containerapp ingress traffic set \
  --revision-weight v2=100
```

### 4. API Versioning

```python
# Support old and new clients simultaneously
@app.get("/api/v1/chat/history")  # Old format
@app.get("/api/v2/chat/history")  # New format with pagination
```

### 5. Distributed Logging

```python
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    logger.bind(correlation_id=correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

### 6. Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(...):
    ...
```

---

## CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build container
        run: az acr build --registry opsiqacr --image opsiq-iis:${{ github.sha }} ./iis
      
      - name: Deploy to staging
        run: az containerapp update --name opsiq-iis-staging --image opsiqacr.azurecr.io/opsiq-iis:${{ github.sha }}
      
      - name: Smoke test
        run: curl -f https://staging-api.opsiq.armanino.com/health
      
      - name: Deploy to production
        if: success()
        run: az containerapp update --name opsiq-iis-prod --image opsiqacr.azurecr.io/opsiq-iis:${{ github.sha }}
```

---

## Next Steps

1. **Pilot Prep**: Configure env-based API URLs, deploy Container Apps
2. **Multi-Platform Auth**: Register all redirect URIs in Entra ID + Workday
3. **Secrets**: Set up Azure Key Vault, migrate secrets from .env
4. **CI/CD**: Create GitHub Actions deployment pipeline
5. **Pre-Production**: Tauri Updater, Azure Front Door, Static Web Apps
6. **Mobile**: Initialize Tauri Mobile for iOS/Android builds
7. **Caching**: Deploy Azure Cache for Redis
8. **Production**: Blue/Green setup, API versioning, PG read replicas
