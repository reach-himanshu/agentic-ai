# Offline Capability and Push Notifications

## Overview

Tauri native apps support offline functionality and push notifications through built-in plugins and platform-specific integrations.

---

## Push Notifications

### Desktop Notifications (Built-in)

Tauri has native notification support out of the box:

```typescript
// Frontend - using Tauri notification API
import { sendNotification, requestPermission } from '@tauri-apps/plugin-notification';

// Request permission first
await requestPermission();

// Send notification
await sendNotification({
  title: 'New Message',
  body: 'John replied to your ServiceNow ticket',
  icon: 'icons/notification.png'
});
```

**Tauri Config** (`tauri.conf.json`):
```json
{
  "plugins": {
    "notification": {
      "all": true
    }
  }
}
```

### Server-Initiated Push Notifications

| Platform | Method | Technology |
|----------|--------|------------|
| Desktop | WebSocket | Persistent connection |
| iOS | APNS | Apple Push Notification Service |
| Android | FCM | Firebase Cloud Messaging |

### WebSocket Push (Desktop - Recommended)

```typescript
// Frontend - WebSocket for real-time notifications
const ws = new WebSocket('wss://api.opsiq.armanino.com/ws/notifications');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  
  // Show native notification
  sendNotification({
    title: notification.title,
    body: notification.body,
    sound: 'default'
  });
};
```

```python
# Backend - FastAPI WebSocket
@app.websocket("/ws/notifications")
async def notification_socket(websocket: WebSocket, user_id: str):
    await websocket.accept()
    
    # Subscribe to user's notification channel
    async for notification in get_user_notifications(user_id):
        await websocket.send_json(notification)
```

---

## Local Storage Options

### Comparison

| Method | Best For | Persistence | Size Limit |
|--------|----------|-------------|------------|
| **Tauri Store Plugin** | Key-value data, settings | ✅ Persistent | ~100 MB |
| **SQLite (via plugin)** | Structured data, queries | ✅ Persistent | Unlimited |
| **localStorage** | Small data, cache | ✅ Persistent | ~5-10 MB |
| **IndexedDB** | Large blobs, offline data | ✅ Persistent | ~50 MB+ |

### Option 1: Tauri Store Plugin (Settings & Preferences)

```typescript
import { Store } from '@tauri-apps/plugin-store';

const store = new Store('.user-data.json');

// Save user preferences
await store.set('preferences', {
  theme: 'dark',
  notifications: true,
  lastSessionId: 'abc123'
});

// Load on app start
const prefs = await store.get('preferences');
```

**Storage Location**:
- Windows: `%APPDATA%\com.opsiq.app\.user-data.json`
- macOS: `~/Library/Application Support/com.opsiq.app/.user-data.json`

### Option 2: SQLite (Structured Data & Offline Cache)

```typescript
import Database from '@tauri-apps/plugin-sql';

const db = await Database.load('sqlite:opsiq.db');

// Create tables
await db.execute(`
  CREATE TABLE IF NOT EXISTS cached_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    content TEXT,
    timestamp DATETIME,
    synced INTEGER DEFAULT 0
  )
`);

// Store messages locally
await db.execute(
  'INSERT INTO cached_messages (id, session_id, content, timestamp) VALUES (?, ?, ?, ?)',
  [message.id, sessionId, message.content, new Date().toISOString()]
);

// Query offline messages
const messages = await db.select(
  'SELECT * FROM cached_messages WHERE session_id = ? ORDER BY timestamp',
  [sessionId]
);
```

---

## Offline-First Architecture

### Sync Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    OFFLINE-FIRST ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   USER ACTION (send message)                                    │
│           │                                                      │
│           ▼                                                      │
│   ┌───────────────────┐                                         │
│   │ Save to Local DB  │  ← Immediate (no network needed)        │
│   │ (synced = false)  │                                         │
│   └─────────┬─────────┘                                         │
│             │                                                    │
│             ▼                                                    │
│   ┌───────────────────┐     ┌───────────────────┐               │
│   │ Try Send to API   │────→│  Success?         │               │
│   └───────────────────┘     └─────────┬─────────┘               │
│                                       │                          │
│                         ┌─────────────┴─────────────┐            │
│                         ▼                           ▼            │
│                    ┌─────────┐                ┌─────────┐        │
│                    │   YES   │                │   NO    │        │
│                    └────┬────┘                └────┬────┘        │
│                         │                          │             │
│                         ▼                          ▼             │
│              ┌─────────────────────┐    ┌─────────────────────┐  │
│              │ Mark synced = true  │    │ Queue for retry     │  │
│              └─────────────────────┘    │ (when online)       │  │
│                                         └─────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```typescript
// src/hooks/useOfflineSync.ts
export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  useEffect(() => {
    const handleOnline = async () => {
      setIsOnline(true);
      await syncPendingMessages();
    };
    
    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, []);
  
  const syncPendingMessages = async () => {
    const unsynced = await localStorage.getUnsyncedMessages();
    
    for (const msg of unsynced) {
      try {
        await fetch('/api/v1/messages', {
          method: 'POST',
          body: JSON.stringify(msg)
        });
        await localStorage.markSynced([msg.id]);
      } catch (e) {
        // Will retry on next sync
      }
    }
  };
  
  return { isOnline, syncPendingMessages };
}
```

---

## Hybrid Storage Service

```typescript
// src/storage/LocalStorage.ts
import { Store } from '@tauri-apps/plugin-store';
import Database from '@tauri-apps/plugin-sql';

class LocalStorage {
  private store: Store;
  private db: Database;
  
  async init() {
    this.store = new Store('.settings.json');
    this.db = await Database.load('sqlite:opsiq-cache.db');
  }
  
  // Settings (key-value)
  async getUserPreferences() {
    return this.store.get('preferences');
  }
  
  async setUserPreferences(prefs: UserPreferences) {
    await this.store.set('preferences', prefs);
  }
  
  // Chat history (structured)
  async getCachedMessages(sessionId: string) {
    return this.db.select(
      'SELECT * FROM messages WHERE session_id = ?',
      [sessionId]
    );
  }
  
  // Offline sync
  async getUnsyncedMessages() {
    return this.db.select('SELECT * FROM messages WHERE synced = 0');
  }
  
  async markSynced(messageIds: string[]) {
    await this.db.execute(
      `UPDATE messages SET synced = 1 WHERE id IN (${messageIds.map(() => '?').join(',')})`,
      messageIds
    );
  }
}

export const localStorage = new LocalStorage();
```

---

## Required Tauri Plugins

### Installation

```bash
npm install @tauri-apps/plugin-notification
npm install @tauri-apps/plugin-store
npm install @tauri-apps/plugin-sql
```

### Cargo.toml (`src-tauri/Cargo.toml`)

```toml
[dependencies]
tauri-plugin-notification = "2"
tauri-plugin-store = "2"
tauri-plugin-sql = { version = "2", features = ["sqlite"] }
```

### main.rs

```rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_sql::Builder::default().build())
        .run(tauri::generate_context!())
        .expect("error running tauri app");
}
```

---

## Platform Summary

| Feature | Desktop (Tauri) | Mobile (Tauri Mobile) |
|---------|-----------------|----------------------|
| **Local Notifications** | ✅ Built-in plugin | ✅ Native |
| **Push Notifications** | WebSocket | FCM/APNS |
| **Key-Value Storage** | ✅ Store plugin | ✅ Store plugin |
| **SQL Database** | ✅ SQLite plugin | ✅ SQLite plugin |
| **Offline Sync** | ✅ Custom pattern | ✅ Same pattern |
