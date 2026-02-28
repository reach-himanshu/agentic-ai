# Ops IQ: Architectural Brainstorming & Strategic Roadmap

This document captures the strategic evolution of the Ops IQ architecture, moving from a multi-hop prototype to a high-performance "Intelligence Service" suitable for enterprise Proof of Value (POV).

---

## 🔍 The Impartial Critique (Common Pitfalls)

| Challenge | Impact | Strategic Response |
| :--- | :--- | :--- |
| **Latency Tax** | 5-6 network hops per request cause significant UI lag. | **Service Collapse**: Merge Orchestrator, BFF, and Core Tools. |
| **Tool Intelligence Duplication** | Logic exists in MCP definitions, BFF gating, and LLM prompts. | **MCP-First Registry**: Dynamic prompt injection from Layer 4. |
| **Schema-to-UI Ceiling** | Generic forms eventually fail to support complex UX requirements. | **Hybrid Manifests**: Allow fallback to custom React components. |
| **WebSocket State Debt** | Stateful connections are fragile and difficult to load balance. | **SSE + REST**: Stream output via SSE; input actions via stateless REST. |
| **Orchestration Overkill** | Large LLMs used for deterministic, repetitive actions. | **Semantic Routing**: Use a fast-path for known tool clicks. |

---

## 🚀 The "Intelligence Service" (POV Strategy)

### 1. Triple-Layer Collapse (BOML Implementation)
Instead of independent services for Orchestration (AutoGen) and Mediation (BFF), we merge them into a single **Intelligence Service** built around a **Business Object Mediation Layer (BOML)**.
- **Local Execution**: Agents call `FastMCP` tools as local Python functions, bypassing HTTP/SSE overhead.
- **Unified Security**: One container, one auth context, one configuration layer.

### 2. Hybrid MCP Connectivity (Hub & Spoke)
- **Core Tools (Local)**: High-frequency tools (D365 Account Lookup, Workday Profile) live inside the Intelligence Service for sub-second response.
- **Remote Tools (Proxy)**: Niche or third-party tools (ServiceNow, DevOps) are connected via SSE/stdio as satellite servers.

### 3. Scaling the Monolith
To scale an integrated service without losing the "Speed of Local":
- **Horizontal Scaling**: Replicate the container using Podman/K8s.
- **Stateless Intelligence**: Move agent memory/history to **Redis** or **Postgres**.
- **Functional Clipping**: If one system (e.g., D365) becomes a bottleneck, "clip" it back into a standalone microservice while keeping the core collapsed.

---

## 🛠️ Definition of Core Tools (Enterprise Standard)

Core tools are prioritized for the "Intelligence Service" based on the **80/20 Rule** (80% of daily user activity).

| Category | Examples |
| :--- | :--- |
| **Daily Pulse** | Customer 360 (D365), Employee Snapshot (Workday), Active Case List. |
| **Actionable Bridge** | New Hire Onboarder (WD -> D365 Sync), Sales Commission Trigger. |
| **Guided Execution** | Structured "Opportunity Closer" Wizard, Batch Time-Off Approver. |
| **Agent Utility** | Policy/Guardrail Lookup, Local Audit Logger. |

---

## 🧠 Brainstorming Consensus: The BOML Advantage

Following our deep dive, we have reached a strategic consensus: **Option A (The BOML Layer)** is the superior path for enterprise reliability. 

### Why BOML over Raw APIs?
- **Process Sovereignity**: Business rules live in version-controlled code, not stochastic prompts.
- **Complexity Abstraction**: The agent orchestrates "Business Outcomes" (e.g., `initiate_onboarding`) rather than "API Methods" (e.g., `POST /employees`).
- **Safety**: Built-in validation happens at the mediation layer, preventing the agent from "hallucinating" invalid data sequences.

### Deterministic Roadmap: Stabilization & Mastery (Phase 11)

Our current focus is on **System Stabilization** to ensure the core foundations are industrial-grade:

1. **Knowledge Hub Mastery**: Full end-to-end verification of metadata CRUD, chunk-level retrieval accuracy, and large document handling.
2. **IIS Discovery Reliability**: Hardening the "Universal Discovery" cues in the chat interface to ensure zero-friction navigation.
3. **Core BOML Stability**: Verifying the existing D365 "Deep Insert" and account lookup tools for 100% reliability.

---

## 🔮 Future Horizon: The "Smart Importer" (Phase 10)

For future development, we have identified the **Smart Importer** as a high-value tool to solve manual Excel-entry bottlenecks through a **Review-then-Commit** (HITL) pattern.

---

> [!TIP]
> **Refined Strategy**: We are prioritizing "Solidifying what we have" over building new ingestion features to ensure a premium user experience from Day 1.
