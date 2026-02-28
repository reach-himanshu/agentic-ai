# D365 CRM: Deterministic Business Flows (Phase 10)

This document outlines the target state for deterministic automation within the D365 CRM ecosystem, bridging the gap between conversational AI and transactional ERP logic.

## 1. Core Schema Reference

| Entity | Required Fields & Type | Relationships |
| :--- | :--- | :--- |
| **Account** | Name, Relationship Type (Option), Industry (Option), Zip, Owner (Lookup) | Parent of Contact, Opportunity |
| **Contact** | FirstName, LastName, Email, Phone | Lookup to Company (Account) |
| **Opportunity** | Name, Potential Customer (Lookup), Primary Contact (Lookup), Lead Source (Option), Sales Team (Option), Sales Stage (Option 0-5), Probability, Close State, Renewal Date, Owner (Lookup), Partner (Lookup) | Linked to Account, Primary Contact |
| **Product & Services** | Service Type (Lookup), Cost Center (Lookup), Value Based Pricing (Bool), Engagement Type (Option), Estimated Revenue | Child of Opportunity |
| **Included Entities** | Service Type, Primary Account, Price Value | Relates Opportunity to delivery targets |

## 2. The Opportunity Lifecycle (Stages 0-5)

Automation triggers at key stage transitions:
- **Stage 2 (Initial Meeting Held)**: Triggers an event to **ServiceNow**.
- **Stage 3 (Value Proposition)**: Triggers information sync to **InTapp (QRM Tool)** for Risk & Compliance.
  - *Conflict Check*: Checks risk/compliance for account/services.
  - *Write-back*: InTapp writes back `CIS Survey Completed` status to CRM (Approved/Rejected).

## 3. CPIF: Customer Project Initiation Form
The CPIF is the final gateway to delivering services, initiated from the **Included Entity** record once a CSR approved.

### Workday Project Setup Integration
The agent pre-fills and validates the following data for Workday:
- **Project Context**: Service Type, Company, Project Hierarchy, Template.
- **Timing**: Month, Start/End Date.
- **Roles**: Customer Collection Lead, Project Delivery Lead, PM, Assistant PM, Billing Specialist.
- **Sync**: XCM Sync flag and XCM Tax Form Number.
- **Contract Details**: Fixed Fee vs T&M, Invoice Type (Single/Multiple), Bill-to Customer, Engagement Letter status.
- **Financials**: Estimated Hours, Contracted Amount, Rate Sheet.

## 4. Deterministic BOML Tools

| Tool Name | Scope | Business Purpose |
| :--- | :--- | :--- |
| **`check_opp_readiness`** | CRM Logic | Validates all mandatory Option Sets and Lookups before allowing Stage 2/3 transitions. |
| **`reconcile_qrm_status`** | InTapp + Hub | If a CIS survey is rejected, cross-references Knowledge Hub rules to propose a remediation plan. |
| **`generate_cpif_proposal`** | Workday + CRM | Aggregates data from Account, Opp, and Included Entity to pre-populate the Workday Project Setup form. |
| **`validate_billing_integrity`** | Workday + XCM | Ensures Contract Type matches Rate Sheet and XCM Tax forms are authorized before closure. |
| **`distribute_entity_revenue`** | Account Logic | Manages the 1-to-many allocation of Opportunity revenue across several Included Entities. |
