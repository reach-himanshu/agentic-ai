# AI Evaluation & Quality Framework

This document defines how we will measure success, detect regressions, and ensure the reliability of the Agentic AI solution using quantitative metrics and a "Golden Dataset."

## Objective
To move from "vibes-based" development to **data-driven engineering** by measuring the agent's accuracy, efficiency, and safety across every release.

## The Evaluation Stack

1. **Framework**: **DeepEval** (Integrated with Pytest).
2. **Methodology**: **LLM-as-a-Judge** (using G-Eval with GPT-4o).
3. **Trigger**: Continuous Integration (CI) on every Pull Request.

## Key Metrics (The Three Layers)

### 1. Reasoning Layer (Strategic)
- **Plan Quality**: Does the proposed sequence of tools logically lead to the user's goal?
- **Plan Adherence**: Does the agent actually follow its own plan, or does it wander?

### 2. Action Layer (Tactical)
- **Tool Correctness**: Did it call the *right* tool (e.g., Workday for payroll, not D365)?
- **Argument Accuracy**: Are the tool parameters (IDs, dates, filters) exact matches for the user's requirement?

### 3. Execution Layer (Outcome)
- **Task Completion**: Did the user actually get their answer or task done?
- **Step Efficiency**: Is the agent taking 10 steps for a 3-step task?

## The "Golden Dataset"
We will maintain a `golden_dataset.json` containing 100+ high-quality test cases across three main domains:

| Domain | Example Query | Expected Tools |
| :--- | :--- | :--- |
| **Workday** | "What is my remaining PTO?" | `get_worker_id`, `get_pto_balance` |
| **D365** | "List accounts in Seattle." | `query_accounts(filter="Seattle")` |
| **ServiceNow** | "Get status of INC00123." | `get_incident_details(id="INC00123")` |

## Implementation Phases

### Phase 1: Metric Definition & Baseline
- [ ] Implement `PlanQualityMetric` and `ToolCorrectnessMetric` in the test suite.
- [ ] Generate an initial baseline score using current system prompts.

### Phase 2: Golden Dataset Creation
- [ ] Interview domain experts to capture 50 complex "edge case" scenarios.
- [ ] Script the synthetic generation of 50 basic scenarios.

### Phase 3: Automated Quality Gates
- [ ] Integrate evaluation into the CI pipeline.
- [ ] Block deployment if "Task Completion" or "Safety" scores drop below 90%.
