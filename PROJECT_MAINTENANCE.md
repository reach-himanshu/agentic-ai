# Project Upkeep and Maintenance Document

This document serves as a Knowledge Transfer (KT) guide for maintaining the Ops IQ Integrated Intelligence Service (IIS). It details each architectural layer, its components, and configuration requirements.

---

## 🏗️ Architectural Layers

### 1. Frontend Layer (React + Vite + Tauri)
The presentation layer is responsible for the user interface, Generative UI rendering, and session management.

*   **Key Components:**
    *   `src/pages/Chat.tsx`: Main chat interface and session orchestration.
    *   `src/components/ChatMessage.tsx`: Renders text, data tables, forms, and pills from UI Manifests.
    *   `src/context/AuthContext.tsx`: Manages authentication state and active LLM model selection.
*   **Configuration:**
    *   `src/config.ts`: Global application metadata (App Name, Description).
    *   `src/authConfig.ts`: MSAL configuration for Entra ID integration.
*   **Maintenance:**
    *   Theme variables are defined in `src/index.css`.
    *   Session state and model choice are persisted in `localStorage`.

### 2. Service Layer (Integrated Intelligence Service - IIS)
A FastAPI-based backend that handles WebSocket/SSE communication, database persistence, and observability initialization.

*   **Key Components:**
    *   `iis/main.py`: Entry point, lifecycle management, and API route definitions.
    *   `iis/core/database.py`: SQLAlchemy Models (ChatSession, ChatMessage) and SQLite setup.
    *   `iis/core/session_store.py`: CRUD operations for chat persistence and agent state serialization.
*   **Configuration:**
    *   `iis/.env`: Contains API keys (Azure, DataDog) and environment flags.
    *   `iis/config.py`: Unified configuration loader for YAML/ENV model definitions.
*   **Maintenance:**
    *   The service uses a stateless pivot model; ensure `session_id` is passed with every request.

### 3. Orchestration Layer (AutoGen)
The logic layer where agents plan and execute tasks.

*   **Key Components:**
    *   `iis/agents/planner.py`: The "Brain". Handles intent detection, security filtering, and plan generation.
    *   `iis/agents/executor.py`: The "Hands". Executes tool calls across D365, Workday, and ServiceNow via BOML.
*   **Configuration:**
    *   Intent prompts are embedded in `PlannerAgent._get_intent`.
    *   Model parameters (temperature, max tokens) are defined in model configuration YAMLs.
*   **Maintenance:**
    *   Update `ExecutorAgent` when new enterprise integrations are added.

### 4. Governance & Security Layer
Automated safety checks for PII and out-of-scope requests.

*   **Key Components:**
    *   `iis/core/pii_redactor.py`: Uses Microsoft Presidio for multi-entity redaction.
    *   `iis/core/guardrails/`: NVIDIA NeMo Guardrails configuration.
    *   `iis/agents/planner.py`: Multi-layered firewall (NeMo -> Custom Fallback).
*   **Configuration:**
    *   `iis/core/guardrails/config.yml`: Policy engine settings.
    *   `iis/core/guardrails/flows.co`: Colang definitions for allowed/blocked topics.
*   **Maintenance:**
    *   Tune PII recognizers in `pii_redactor.py` if false positives/negatives occur.
    *   Inhibit or allow new topics by updating `flows.co`.

### 5. Observability Layer (DataDog & OTel)
Comprehensive tracing and metrics collection.

*   **Key Components:**
    *   `iis/core/observability.py`: OpenTelemetry setup with custom Span/Log processors.
    *   `deploy_dashboard.py`: Automation script to create/update DataDog dashboards.
*   **Configuration:**
    *   `datadog_agent_insights.json`: JSON template for the DataDog dashboard.
    *   `OTEL_EXPORTER_OTLP_ENDPOINT`: Points to the DataDog agent or API.
*   **Maintenance:**
    *   Run `python deploy_dashboard.py` whenever the JSON template is modified.

### 6. Integration Layer (BOML)
The Business Object Mediation Layer for enterprise systems.

*   **Key Components:**
    *   `iis/integrations/`: Subdirectories for D365, Workday, ServiceNow.
    *   `router.py`: FastAPI routers exposing specialized tool endpoints.
*   **Maintenance:**
    *   Update API versions and base URLs in the respective integration routers.

---

## 🛠️ Operational Maintenance Tasks

1.  **Dependency Updates:** Periodic `pip install -U` within the `iis` virtual environment.
2.  **Database Migration:** If schema changes occur in `database.py`, use Alembic or the `migrate_db.py` utility.
3.  **Model Rotation:** Update model IDs in the configuration YAMLs when migrating from older GPT versions.
4.  **Security Review:** Periodically test the firewall using `test_firewall_repro.py`.
