# Advanced Security & Governance Blueprint

This document defines the high-level security architecture and governance standards for the Agentic AI solution, ensuring it is production-ready, compliant, and resilient.

## 1. Identity & "On-Behalf-Of" (OBO) Authorization
To prevent "Escalated Privilege" attacks, the Agent must never use its own service principal for data access.
- **Pattern**: **OAuth 2.0 OBO Flow**.
- **Enforcement**: When an Agent calls an MCP Tool (e.g., Workday), the IIS backend exchanges the user's Entra ID token for a scoped downstream token.
- **Result**: Data access is strictly limited to the human user's actual entitlements.

## 2. Wallet Exhaustion & Operational Resilience
Protects against "Denial of Wallet" (DoW) attacks where loops or spam drain the Azure/LLM budget.
- **Token-Aware Rate Limiting**: Implement limits based on **TOKENS per minute**, not just requests.
- **Per-User Quotas**: Set hard daily/monthly budget caps per persona or department.
- **Circuit Breakers**: Automatically kill an agent quest if it goes beyond 5 consecutive "thoughts" or "tool calls" without human feedback.

## 3. Indirect Prompt Injection (Tool Poisoning)
Protects against malicious data found *inside* tools (e.g., a "poisonous" CRM record).
- **Context Isolation**: Use clear XML-style delimiters (e.g., `<tool_output>...</tool_output>`) to ensure the LLM distinguishes between its instructions and external data.
- **Read-Only Default**: All MCP tool endpoints are read-only by default. Proactive actions (Create/Update/Delete) require an explicit **HITL (Human-in-the-Loop)** approval pill.

## 4. Secret Management & Data Sovereignty
Ensures sensitive credentials and data are handled according to enterprise policy (GDPR/SOC2).
- **Vaulting**: All API Keys and Tool Secrets are stored in **Azure Key Vault**.
- **Managed Identities**: No credentials reside in code or environment variables; the IIS service uses System-Assigned Managed Identity to access the vault.
- **Residency**: IIS and LLM instances are deployed in region-locked clusters (e.g., US-East, North-Europe) to satisfy data residency laws.

## 5. Audit Logging & Non-Repudiation
Ensures every action is traceable to both an Agent and a Human.
- **Signed HITL**: Every "Confirm" action in the UI generates a cryptographically signed event package containing the User ID, Timestamp, and the exact Plan being approved.
- **Immutable Log Store**: Logs are pushed to an immutable storage sink (e.g., Azure Blob with WORM policy) for forensic audits.

---

> [!IMPORTANT]
> This blueprint, combined with the **Observability** and **Guardrails** strategies, creates a "Defense-in-Depth" posture specifically tailored for the dynamic nature of Agentic AI.
