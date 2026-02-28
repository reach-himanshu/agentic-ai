# Development vs. Deployment Notes

## Overview

This document clarifies the difference between development requirements and end-user requirements for the AI Agent Desktop App.

---

## Requirements Summary

| Environment | Node.js | Rust/Cargo | WebView2 | What's Needed |
|-------------|---------|------------|----------|---------------|
| **Development Machine** | ✅ Required | ✅ Required (for Tauri) | ✅ Required | Full toolchain |
| **End User Machine** | ❌ Not needed | ❌ Not needed | ✅ Pre-installed on Windows 10/11 | Just the `.exe` |

---

## Development Environment Setup

### Required Tools

1. **Node.js** (LTS version)
   - Used for: React development, Vite bundling, npm packages
   - Download: https://nodejs.org/

2. **Rust & Cargo**
   - Used for: Tauri compilation, building the native wrapper
   - Download: https://rustup.rs/

3. **Visual Studio Build Tools** (Windows)
   - Used for: Compiling native dependencies
   - Included with Visual Studio or can be installed separately

### Development Workflow

```
npm run dev      → Runs React dev server (localhost:5173)
npm run build    → Builds production React bundle
npm run tauri dev    → Runs app in Tauri dev mode (with hot reload)
npm run tauri build  → Creates distributable .exe
```

---

## How Tauri Bundles the App

```
┌─────────────────────────────────────────────────────────────┐
│                     Build Process                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  React Source (.tsx)                                         │
│        ↓                                                     │
│  Vite Build                                                  │
│        ↓                                                     │
│  Static Assets (HTML, CSS, JS)                               │
│        ↓                                                     │
│  Tauri Compiler (Rust)                                       │
│        ↓                                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Final .exe (~10-15 MB)                     │ │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐  │ │
│  │  │ Rust Runtime    │  │ Embedded Static Assets      │  │ │
│  │  │ (Tauri Core)    │  │ (Your React App)            │  │ │
│  │  └─────────────────┘  └─────────────────────────────┘  │ │
│  │                                                         │ │
│  │  Uses system WebView2 (not bundled, already on Windows) │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## End User Experience

### What They Receive
- A single `.exe` file (or `.msi` installer if preferred)
- Optionally: Auto-update capability via Tauri's updater plugin

### What They Need
- Windows 10 or Windows 11
- WebView2 runtime (pre-installed on Windows 10 1803+ and all Windows 11)

### Installation Steps for End User
1. Download the `.exe`
2. Double-click to run
3. That's it! No installation of Node.js, Rust, or any other tools required.

---

## Comparison with Other Desktop Frameworks

| Framework | End User Requirements | App Size | Memory Usage |
|-----------|----------------------|----------|--------------|
| **Tauri** (our choice) | WebView2 (pre-installed) | ~10-15 MB | Low |
| **Electron** | Nothing (bundles Chromium) | ~100-150 MB | High |
| **React Native Windows** | .NET runtime (usually pre-installed) | ~30-50 MB | Medium |
| **Flutter Windows** | Nothing | ~20-30 MB | Medium |

---

## Key Takeaways

1. **Development requires a full toolchain** (Node.js, Rust, build tools)
2. **End users only need the compiled `.exe`** - no additional software required
3. **Tauri produces small, efficient executables** by using the system's native WebView2
4. **Auto-updates can be added** via `tauri-plugin-updater` for seamless updates post-deployment
