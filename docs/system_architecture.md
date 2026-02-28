# Ops IQ: System Architecture (POV Target State)

This document visualizes the high-performance **Integrated Intelligence Service (IIS)** architecture, which collapses orchestration, identity mediation, and core business tools into a unified execution layer.

## 🏗️ 4-Layer Architecture (Integrated)

```mermaid
graph TD
    subgraph "Layer 1: Presentation (Frontend)"
        FE_UI["Chat Interface (React + Tauri)"]
        FE_JIT["JIT UI Engine (Manifest Renderer)"]
        FE_AUTH["MSAL Provider (Entra ID)"]
    end

    subgraph "Integrated Intelligence Service (Core Stack)"
        direction TB
        subgraph "Ingest & Safety"
            PRE["PII Redactor (Presidio)"]
            FIREWALL["Semantic Firewall (NeMo)"]
        end

        subgraph "Orchestration"
            ORC_AG["AutoGen Agents (Planner/Executor)"]
            MANIFEST["UI Manifest Generator"]
            DISCOVERY["Discovery Manifest Sync"]
        end

        subgraph "Identity & Persistence"
            OBO["Identity Mediator (OBO Flows)"]
            CONTEXT["Scoped Context Manager"]
            DB[("Session Store (PostgreSQL/asyncpg)")]
        end

        subgraph "BOML: Business Object Mediation Layer"
            BFF["FastAPI Gateway / BFF"]
            D365_CORE["Dynamics 365 (OBO/CC)"]
            WD_CORE["Workday (Financials)"]
            SNOW_CORE["ServiceNow (OBO)"]
        end
    end

    subgraph "Layer 4: Remote Satellites"
        LIB["Librarian RAG Gateway"]
        WEAV[("Knowledge Base (Weaviate)")]
        M365["Microsoft Graph (Graph API/OBO)"]
        DD["Observability (DataDog)"]
    end

    %% Flow Relationships
    User((User)) --> FE_UI
    FE_UI <-->|OAuth2 + WebSocket| BFF
    FE_AUTH -- Token --> FE_UI
    
    BFF --> PRE
    PRE --> FIREWALL
    FIREWALL --> ORC_AG
    ORC_AG --> MANIFEST
    MANIFEST --> DISCOVERY
    
    ORC_AG <-->|Identity Context| OBO
    OBO <-->|Token Exchange| M365
    
    BFF --- DB
    
    BFF --> D365_CORE
    BFF --> WD_CORE
    BFF --> SNOW_CORE
    BFF --> LIB
    LIB <-->|Vector Search| WEAV

    %% Observability Tapping
    IIS["Integrated Intelligence Service"] -.->|Spans & Logs| DD

    %% Styling
    style FE_UI fill:#6366f1,color:#fff
    style BFF fill:#06b6d4,color:#fff
    style PRE fill:#8b5cf6,color:#fff
    style FIREWALL fill:#ef4444,color:#fff
    style ORC_AG fill:#f59e0b,color:#fff
    style DB fill:#10b981,color:#fff
    style DD fill:#7c3aed,color:#fff
    style WEAV fill:#00d685,color:#fff
```

---

## 📋 Technical Component Mapping

| Layer | Technical Name / Component | Purpose |
| :--- | :--- | :--- |
| **Presentation** | **React (Vite) + Tauri** | Premium desktop shell with MSAL.js integration for Entra ID authentication. |
| | **JIT UI Engine** | Renders structured payloads (`table`, `form`, `pills`) using the **SafeRender (Stringify Guard)** pattern. |
| **Orchestration** | **AutoGen 0.7.x** | Multi-agent framework orchestrating the **Planner** (Reasoning) and **Executor** (Tools). |
| | **Discovery Sync** | Deterministic synchronization of "Area" and "Tool" selection pills to guide user intent. |
| **Identity** | **OBO (On-Behalf-Of)** | Centralized token exchange for downstream resources like MS Graph and ServiceNow. |
| | **Scoped Context** | Python thread-local storage propagating user permissions and tokens across agent tasks. |
| **Safety** | **PII Redactor (Presidio)** | Multi-entity sensitive data masking across all logs, traces, and LLM payloads. |
| | **Semantic Firewall** | Multi-layered protection using **NeMo Guardrails** and custom LLM domain classifiers. |
| **Knowledge Hub** | **Librarian Gateway** | FastAPI service managing document chunking and metadata. Supports **Active/Deactivated/Deleted** states. |
| | **Weaviate + text2vec** | On-premises vector storage with local transformer-based embedding generation. |
| **Persistence** | **PostgreSQL (asyncpg)** | High-performance, async central database for session retention (Last 20 sessions / 5 days). |
| **Mediation** | **BOML Layer** | Standardized mediation for D365, Workday, and ServiceNow. Supports **OBO & Client-Credentials** with **Multi-Tenant/Multi-Environment** resolution for D365. |

---

> [!IMPORTANT]
> **Identity Consolidation**: All downstream tools must use the `auth_user_ctx` to ensure data access respects the authenticated user's permissions.

> [!TIP]
> **Mermaid Preview**: Use the [Mermaid Live Editor](https://mermaid.live/) to visualize or modify the flow diagram asynchronously.
