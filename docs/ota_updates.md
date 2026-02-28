# Over-The-Air (OTA) Updates

## Overview

OTA updates enable "Restart to Update" functionality like VS Code and Chrome, where the app downloads updates in the background and prompts users to restart when ready.

---

## How OTA Updates Work

```
┌─────────────────────────────────────────────────────────────────┐
│                    OTA UPDATE FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. APP STARTS                                                  │
│      └── Check https://releases.opsiq.armanino.com/latest.json  │
│                                                                  │
│   2. COMPARE VERSIONS                                            │
│      └── Current: 1.0.0  |  Latest: 1.1.0  →  Update available! │
│                                                                  │
│   3. DOWNLOAD IN BACKGROUND                                      │
│      └── Download MSI/DMG while user works (no interruption)    │
│                                                                  │
│   4. NOTIFY USER                                                 │
│      ┌─────────────────────────────────────────────────────┐    │
│      │ 🔄 Update available!                                │    │
│      │    Version 1.1.0 is ready to install.               │    │
│      │    [Restart Now]  [Later]                           │    │
│      └─────────────────────────────────────────────────────┘    │
│                                                                  │
│   5. USER CLICKS "RESTART NOW"                                   │
│      └── App closes → Installer runs → New version launches     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tauri Configuration

### `tauri.conf.json`

```json
{
  "productName": "Ops IQ",
  "version": "1.0.0",
  "plugins": {
    "updater": {
      "endpoints": [
        "https://releases.opsiq.armanino.com/latest.json"
      ],
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk..."
    }
  }
}
```

### Generate Signing Keys

```bash
# Generate a keypair for signing updates
npx tauri signer generate -w ~/.tauri/opsiq.key

# Output:
# Public key: dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYya...
# Private key saved to: ~/.tauri/opsiq.key
```

> ⚠️ **Keep the private key secret!** Store it in Azure Key Vault or GitHub Secrets.

### Build Signed Updates

```bash
# Set the private key as environment variable
$env:TAURI_SIGNING_PRIVATE_KEY = Get-Content ~/.tauri/opsiq.key

# Build with signing
npm run tauri build

# Output:
# src-tauri/target/release/bundle/
#   ├── msi/Ops_IQ_1.1.0_x64_en-US.msi
#   └── msi/Ops_IQ_1.1.0_x64_en-US.msi.sig  ← Signature file
```

### Update Manifest (`latest.json`)

```json
{
  "version": "1.1.0",
  "notes": "Bug fixes and performance improvements",
  "pub_date": "2026-01-15T00:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJp...",
      "url": "https://releases.opsiq.armanino.com/Ops_IQ_1.1.0_x64_en-US.msi.zip"
    },
    "darwin-x86_64": {
      "signature": "...",
      "url": "https://releases.opsiq.armanino.com/Ops_IQ_1.1.0_x64.app.tar.gz"
    },
    "darwin-aarch64": {
      "signature": "...",
      "url": "https://releases.opsiq.armanino.com/Ops_IQ_1.1.0_aarch64.app.tar.gz"
    }
  }
}
```

---

## Frontend Implementation

### Update Notification Component

```typescript
// src/components/UpdateNotification.tsx
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';
import { useState, useEffect } from 'react';

export function UpdateNotification() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [readyToInstall, setReadyToInstall] = useState(false);

  useEffect(() => {
    checkForUpdates();
  }, []);

  const checkForUpdates = async () => {
    try {
      const update = await check();
      
      if (update?.available) {
        setUpdateAvailable(true);
        
        // Start background download
        setDownloading(true);
        
        await update.downloadAndInstall((progress) => {
          if (progress.event === 'Progress') {
            const percent = (progress.data.chunkLength / progress.data.contentLength) * 100;
            setDownloadProgress(percent);
          }
        });
        
        setDownloading(false);
        setReadyToInstall(true);
      }
    } catch (error) {
      console.error('Update check failed:', error);
    }
  };

  const handleRestart = async () => {
    await relaunch();
  };

  if (!updateAvailable) return null;

  return (
    <div className="update-banner">
      {downloading && (
        <div className="update-downloading">
          <span>Downloading update...</span>
          <progress value={downloadProgress} max={100} />
        </div>
      )}
      
      {readyToInstall && (
        <div className="update-ready">
          <span>🎉 Update ready!</span>
          <button onClick={handleRestart} className="restart-button">
            Restart to Update
          </button>
          <button onClick={() => setUpdateAvailable(false)} className="later-button">
            Later
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## Telemetry & Analytics

### Track Installations and Active Users

| Metric | Purpose |
|--------|---------|
| Total Installations | Know user base size |
| Active Users (DAU/MAU) | Engagement tracking |
| Version Distribution | Rollout progress |
| Who's Connected Now | Real-time monitoring |

### Installation ID Generation

```typescript
// src/utils/installationId.ts
import { Store } from '@tauri-apps/plugin-store';
import { v4 as uuidv4 } from 'uuid';

export async function getInstallationId(): Promise<string> {
  const store = new Store('.app-config.json');
  let id = await store.get<string>('installationId');
  
  if (!id) {
    id = uuidv4();
    await store.set('installationId', id);
  }
  
  return id;
}
```

### Registration & Heartbeat

```typescript
// src/hooks/useTelemetry.ts
export async function registerInstallation(userId: string) {
  const installId = await getInstallationId();
  const version = await getVersion();
  
  await fetch('/api/v1/telemetry/register', {
    method: 'POST',
    body: JSON.stringify({
      installation_id: installId,
      user_id: userId,
      version: version,
      platform: await platform()
    })
  });
}

export function useHeartbeat(userId: string) {
  useEffect(() => {
    const sendHeartbeat = async () => {
      await fetch('/api/v1/telemetry/heartbeat', {
        method: 'POST',
        body: JSON.stringify({
          installation_id: await getInstallationId(),
          user_id: userId,
          version: await getVersion()
        })
      });
    };
    
    sendHeartbeat();
    const interval = setInterval(sendHeartbeat, 5 * 60 * 1000); // Every 5 min
    
    return () => clearInterval(interval);
  }, [userId]);
}
```

### Backend Telemetry Endpoints

```python
@app.get("/api/v1/telemetry/stats")
async def get_telemetry_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    
    return {
        "total_installations": await count_total(db),
        "active_now": await count_active_in_window(db, minutes=10),
        "daily_active_users": await count_active_in_window(db, hours=24),
        "version_distribution": await get_version_counts(db)
    }
```

---

## Staged Rollouts

### Targeting Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROLLOUT TARGETING HIERARCHY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CHECK ORDER (first match wins):                               │
│                                                                  │
│   1. BLOCKLIST - Skip update if user in blocklist               │
│   2. ALLOWLIST - Always get update (beta testers)               │
│   3. ATTRIBUTE RULES - Department, role, location               │
│   4. PERCENTAGE - Dynamic hash-based rollout                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Targeting Options

| Method | Use Case | How It Works |
|--------|----------|--------------|
| **Allowlist** | Beta testers, specific users | Explicit list of emails/user IDs |
| **Blocklist** | Exclude executives, critical users | Explicit exclusion list |
| **Attribute Rules** | Department, role, location | Match user metadata |
| **Percentage** | Fair random rollout | Hash installation ID to group 0-99 |

### Database Schema

```python
class RolloutConfig(Base):
    __tablename__ = "rollout_configs"
    
    id = Column(Integer, primary_key=True)
    version = Column(String, unique=True)
    percentage = Column(Integer, default=0)      # 0-100
    blocked = Column(Boolean, default=False)
    allowlist = Column(JSON, default=[])         # Always get update
    blocklist = Column(JSON, default=[])         # Never get update
    attribute_rules = Column(JSON, default={})   # {"departments": [...], "roles": [...]}
```

### Smart Update Check Endpoint

```python
@app.get("/api/v1/updates/check")
async def check_for_update(installation_id: str, user_id: str, current_version: str):
    config = await get_rollout_config(latest_version)
    user = await get_user_info(installation_id)
    
    # 1. Blocklist check
    if user_id in config.blocklist:
        return {"update_available": False}
    
    # 2. Allowlist check
    if user_id in config.allowlist:
        return build_update_response(config)
    
    # 3. Attribute rules
    if user.department in config.attribute_rules.get("departments", []):
        return build_update_response(config)
    
    # 4. Percentage rollout
    user_group = hash(installation_id) % 100
    if user_group < config.percentage:
        return build_update_response(config)
    
    return {"update_available": False}
```

### Example Rollout Schedule

| Day | Action | Coverage |
|-----|--------|----------|
| 1 | Add beta testers to allowlist | 5-10 users |
| 2-3 | Add Engineering & QA departments | ~50 users |
| 4 | Set percentage to 25% | ~250 users |
| 5 | Set percentage to 50% | ~500 users |
| 7 | Set percentage to 100% | All users |

### Admin API

```python
# Add beta testers
POST /api/v1/admin/rollout/1.1.0/allowlist
{ "users": ["john@armanino.com", "jane@armanino.com"] }

# Set department targeting
POST /api/v1/admin/rollout/1.1.0/rules
{ "departments": ["Engineering", "QA"] }

# Set rollout percentage
POST /api/v1/admin/rollout/1.1.0
{ "percentage": 50 }

# Emergency: Pause rollout
POST /api/v1/admin/rollout/1.1.0/pause

# Preview who would get update
GET /api/v1/admin/rollout/1.1.0/preview
```

---

## CI/CD: Automated Release Pipeline

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        platform: [windows-latest, macos-latest]
    
    runs-on: ${{ matrix.platform }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Tauri app
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          tagName: v__VERSION__
          releaseName: 'Ops IQ v__VERSION__'
      
      - name: Upload to Azure Blob
        run: |
          az storage blob upload-batch \
            --source ./src-tauri/target/release/bundle \
            --destination releases
```

---

## Update Strategies

| Strategy | User Experience | Best For |
|----------|-----------------|----------|
| **Silent Background** | Download silently, prompt when ready | Most users |
| **Prompt Before Download** | Ask before downloading | Metered connections |
| **Forced Update** | Immediate install for critical fixes | Security patches |

---

## Summary

| Component | Purpose |
|-----------|---------|
| `tauri.conf.json` | Configure updater endpoint + public key |
| Signing keys | Ensure updates are from trusted source |
| `latest.json` | Manifest with version, URLs, signatures |
| Frontend component | UI for "Restart to Update" |
| Telemetry endpoints | Track installations, active users |
| Rollout targeting | Control who gets updates and when |
| CI/CD pipeline | Automate build, sign, publish |
