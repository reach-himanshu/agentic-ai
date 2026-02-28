# AI Agent Prototype - Task Tracker

## Phase 0: Instant Gratification (Working UI First!)

### Project Setup
- [x] 0.1 Initialize React + Vite + TypeScript project
- [x] 0.2 Create design system with dark mode and modern aesthetics
- [x] 0.3 Build mock login screen with Entra ID simulation
- [x] 0.4 Create main chat interface shell
- [x] 0.5 Build ConfirmationCard component (Generative UI)
- [x] 0.6 Integrate Tauri for Windows .exe packaging

---

## Phase 1: API Contracts & Backend
- [x] 1.1 Define OpenAPI spec + MCP tool definitions
- [x] 1.2 Set up FastAPI with Anthropic MCP SDK
- [x] 1.3 Implement auth middleware (JWT validation, role extraction)
- [x] 1.4 Implement MCP endpoints (lookup_client, update_stage, assign_owner)
- [x] 1.5 Create plan loader with YAML + rule engine

---

## Phase 2: Agent Orchestration
- [x] 2.1 Initialize AutoGen setup
- [x] 2.2 Build Executor Agent with MCP tool bindings
- [x] 2.3 Build Planner Agent with HITL pause logic
- [x] 2.4 Implement WebSocket bridge to frontend

---

## Phase 3: Integration
- [x] 3.1 Connect frontend to agent via WebSocket
- [x] 3.2 Implement Generative UI flow (Agent → JSON → Card → Response)
- [x] 3.3 End-to-end testing (Scripted & Manual)
- [x] 3.4 Add LLM & Deployment hint to UI

---

## Phase 4: Security Verification
- [x] 4.1 Admin persona full workflow test
- [x] 4.2 Sales persona restriction test (403 on unauthorized actions)

---

## Phase 5: Persona Expansion
- [x] 5.1 Implement "General User" persona (mock user + frontend login)
- [x] 5.2 Verify general Q&A functionality for non-privileged users
- [ ] 5.3 Enhance intent detection to distinguish between general chat and business plans
