# Productization Strategy: Internal Tool to Commercial SaaS

## Executive Summary

This document analyzes the gaps and requirements for transforming Ops IQ from an internal Armanino tool into a commercial SaaS product that can be sold to other professional services firms.

---

## The Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVOLUTION PATH                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   PHASE 1: INTERNAL TOOL (Current)                              │
│   └── Ops IQ for Armanino                                       │
│   └── Single tenant, custom integrations                        │
│                                                                  │
│   PHASE 2: PRODUCTIZED PLATFORM                                 │
│   └── "Ops IQ for Professional Services"                        │
│   └── Multi-tenant SaaS                                         │
│   └── Sold to other accounting/consulting firms                 │
│                                                                  │
│   PHASE 3: PLATFORM ECOSYSTEM                                   │
│   └── Marketplace for connectors                                │
│   └── Partner integrations                                      │
│   └── API-first platform                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Gap Analysis Summary

| Gap | Current State | Required State | Priority |
|-----|---------------|----------------|----------|
| Multi-tenancy | Single tenant | Tenant isolation | 🔴 Critical |
| White-labeling | Armanino branding | Configurable | 🔴 Critical |
| Billing | None | Stripe integration | 🔴 Critical |
| Admin portal | None | Self-service | 🔴 Critical |
| Security certs | Internal only | SOC 2 Type II | 🟠 Important |
| Connector marketplace | Hard-coded | Pluggable | 🟠 Important |
| SLA/Support | Ad-hoc | Formal | 🟡 Good to have |
| Data residency | Single region | Multi-region | 🟡 Good to have |

---

## Critical Gaps (Must Address Before Selling)

### 1. Multi-Tenancy Architecture

**Current State**: Single-tenant (Armanino only)  
**Required**: Full tenant isolation

```
CURRENT (Single Tenant)
─────────────────────────────────────────
┌───────────────────┐
│    Armanino       │
│    Database       │
│  (All users)      │
└───────────────────┘

REQUIRED (Multi-Tenant)
─────────────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│                      OPS IQ PLATFORM                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Tenant A     │  │ Tenant B     │  │ Tenant C     │       │
│  │ (Armanino)   │  │ (Firm B)     │  │ (Firm C)     │       │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │       │
│  │ │ Database │ │  │ │ Database │ │  │ │ Database │ │       │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │       │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │       │
│  │ │ Secrets  │ │  │ │ Secrets  │ │  │ │ Secrets  │ │       │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

#### Multi-Tenancy Options

| Approach | Isolation | Cost | Complexity | Recommendation |
|----------|-----------|------|------------|----------------|
| Database-per-tenant | Highest | High | Medium | Enterprise tier |
| Schema-per-tenant | High | Medium | Medium | **Default** |
| Row-level security | Medium | Low | High | Starter tier |

#### Implementation

```python
# Multi-tenant middleware
class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        tenant_id = self.extract_tenant_from_domain_or_header(request)
        
        if not tenant_id:
            return JSONResponse(status_code=400, content={"error": "Tenant not found"})
        
        request.state.tenant_id = tenant_id
        request.state.db_schema = f"tenant_{tenant_id}"
        
        return await call_next(request)

# Tenant-isolated repository
class TenantRepository:
    def __init__(self, tenant_id: str, db: AsyncSession):
        self.tenant_id = tenant_id
        self.db = db
    
    async def get_users(self) -> list[User]:
        # Always filter by tenant - cannot access other tenants
        return await self.db.execute(
            select(User).where(User.tenant_id == self.tenant_id)
        )
    
    async def search_knowledge(self, query: str):
        # Vector search limited to tenant's namespace
        return await vector_db.search(
            query=query,
            namespace=f"tenant-{self.tenant_id}",
            filter={"tenant_id": self.tenant_id}
        )
```

---

### 2. White-Labeling & Branding

**Current State**: Armanino branding only  
**Required**: Customer-configurable branding

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHITE-LABEL CONFIG                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TENANT A (Armanino)           TENANT B (Customer Firm)         │
│  ┌────────────────────────┐    ┌────────────────────────┐       │
│  │ [Armanino Logo]        │    │ [Customer Logo]        │       │
│  │                        │    │                        │       │
│  │ Ops IQ                 │    │ SmartAssist Pro        │       │
│  │                        │    │                        │       │
│  │ Colors: #1976D2        │    │ Colors: #4CAF50        │       │
│  │ Font: Inter            │    │ Font: Roboto           │       │
│  └────────────────────────┘    └────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Branding Configuration Schema

```json
{
  "tenant_id": "customer-firm",
  "branding": {
    "product_name": "SmartAssist Pro",
    "logo_url": "https://cdn.customerfirm.com/logo.svg",
    "logo_dark_url": "https://cdn.customerfirm.com/logo-dark.svg",
    "favicon_url": "https://cdn.customerfirm.com/favicon.ico",
    "primary_color": "#4CAF50",
    "secondary_color": "#2196F3",
    "accent_color": "#FF9800",
    "font_family": "Roboto",
    "font_url": "https://fonts.googleapis.com/css2?family=Roboto"
  },
  "domain": {
    "custom_domain": "smartassist.customerfirm.com",
    "subdomain": "customerfirm.opsiq.ai"
  },
  "features": {
    "time_entry": true,
    "knowledge_hub": true,
    "service_now": false,
    "d365": true
  },
  "legal": {
    "privacy_policy_url": "https://customerfirm.com/privacy",
    "terms_url": "https://customerfirm.com/terms"
  }
}
```

#### Frontend Implementation

```typescript
// src/hooks/useBranding.ts
export function useBranding() {
  const [branding, setBranding] = useState<BrandingConfig>(defaultBranding);
  
  useEffect(() => {
    const tenantId = getTenantFromDomain();
    fetch(`/api/v1/branding/${tenantId}`)
      .then(res => res.json())
      .then(config => {
        setBranding(config);
        document.documentElement.style.setProperty('--primary-color', config.primary_color);
        document.documentElement.style.setProperty('--secondary-color', config.secondary_color);
        document.title = config.product_name;
      });
  }, []);
  
  return branding;
}
```

---

### 3. Connector Marketplace

**Current State**: Hard-coded integrations (ServiceNow, D365, Workday)  
**Required**: Pluggable, tenant-configurable connectors

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTOR MARKETPLACE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CORE CONNECTORS (Included in all plans)                       │
│   ├── Microsoft 365 (Calendar, Email)                           │
│   ├── Azure Entra ID (SSO)                                      │
│   └── Knowledge Hub (RAG)                                       │
│                                                                  │
│   PREMIUM CONNECTORS (Per-connector pricing)                    │
│   ├── Workday (Time Entry, HR)                   $5/user/mo    │
│   ├── ServiceNow (ITSM)                          $5/user/mo    │
│   ├── Dynamics 365 (CRM, Finance)                $5/user/mo    │
│   ├── Salesforce                                 $5/user/mo    │
│   ├── NetSuite                                   $5/user/mo    │
│   ├── SAP SuccessFactors                         $5/user/mo    │
│   └── Jira / Confluence                          $3/user/mo    │
│                                                                  │
│   PARTNER CONNECTORS (Revenue share)                            │
│   ├── Industry-specific tools                                   │
│   └── Regional systems                                          │
│                                                                  │
│   CUSTOM CONNECTOR SDK                                          │
│   └── Bring Your Own Integration                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Connector Abstraction

```python
# Base connector interface
class BaseConnector(ABC):
    @abstractmethod
    async def configure(self, tenant_id: str, credentials: dict) -> bool:
        """Configure connector with tenant credentials."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if connector is properly configured."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> list[Tool]:
        """List available MCP tools."""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, params: dict) -> dict:
        """Execute an MCP tool."""
        pass

# Connector registry
class ConnectorRegistry:
    _connectors: dict[str, type[BaseConnector]] = {}
    
    @classmethod
    def register(cls, name: str):
        def decorator(connector_class: type[BaseConnector]):
            cls._connectors[name] = connector_class
            return connector_class
        return decorator
    
    @classmethod
    def get_for_tenant(cls, tenant_id: str) -> dict[str, BaseConnector]:
        enabled = get_tenant_enabled_connectors(tenant_id)
        credentials = get_tenant_credentials(tenant_id)
        
        instances = {}
        for name in enabled:
            if name in cls._connectors:
                connector = cls._connectors[name]()
                connector.configure(tenant_id, credentials.get(name, {}))
                instances[name] = connector
        
        return instances

# Example connector implementation
@ConnectorRegistry.register("servicenow")
class ServiceNowConnector(BaseConnector):
    async def configure(self, tenant_id: str, credentials: dict) -> bool:
        self.instance_url = credentials["instance_url"]
        self.client_id = credentials["client_id"]
        self.client_secret = credentials["client_secret"]
        return True
    
    async def list_tools(self) -> list[Tool]:
        return [
            Tool(name="list_incidents", description="List ServiceNow incidents"),
            Tool(name="create_incident", description="Create a new incident"),
            Tool(name="update_incident", description="Update an existing incident"),
        ]
```

---

### 4. Self-Service Onboarding

**Current State**: Manual setup  
**Required**: Automated tenant provisioning

```
CUSTOMER ONBOARDING FLOW
─────────────────────────────────────────────────────────────────

1. SIGN UP (Self-service)
   └── Customer visits signup.opsiq.ai
   └── Enters company info, admin email
   └── Selects plan (Free trial → Paid)
   └── Accepts terms of service

2. AUTOMATIC PROVISIONING (< 5 minutes)
   ├── Create tenant record
   ├── Provision database schema
   ├── Create admin user
   ├── Generate API keys
   ├── Set up subdomain (customer.opsiq.ai)
   ├── Initialize Knowledge Hub namespace
   └── Send welcome email with setup guide

3. GUIDED SETUP WIZARD
   ├── Step 1: Connect Azure Entra ID (SSO)
   ├── Step 2: Configure branding (logo, colors)
   ├── Step 3: Enable connectors (Workday, ServiceNow)
   ├── Step 4: Configure connector credentials
   ├── Step 5: Import first batch of users (CSV or SCIM)
   └── Step 6: Deploy desktop app to users

4. GO LIVE
   └── Customer deploys desktop app to users
   └── Users sign in with existing SSO
   └── Usage tracking begins
```

#### Provisioning Service

```python
class TenantProvisioningService:
    async def provision_tenant(self, signup: TenantSignup) -> Tenant:
        """Fully automated tenant provisioning."""
        
        # 1. Create tenant record
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=signup.company_name,
            subdomain=self.generate_subdomain(signup.company_name),
            plan=signup.plan,
            status="provisioning"
        )
        await self.db.add(tenant)
        
        # 2. Create database schema
        await self.create_tenant_schema(tenant.id)
        
        # 3. Create admin user
        admin = User(
            tenant_id=tenant.id,
            email=signup.admin_email,
            role="admin"
        )
        await self.db.add(admin)
        
        # 4. Generate API keys
        api_key = await self.generate_api_key(tenant.id)
        
        # 5. Initialize Knowledge Hub namespace
        await self.vector_db.create_namespace(f"tenant-{tenant.id}")
        
        # 6. Set up subdomain SSL
        await self.ssl_service.provision_certificate(tenant.subdomain)
        
        # 7. Send welcome email
        await self.email_service.send_welcome(
            to=signup.admin_email,
            tenant=tenant,
            setup_url=f"https://{tenant.subdomain}.opsiq.ai/setup"
        )
        
        tenant.status = "active"
        await self.db.commit()
        
        return tenant
```

---

### 5. Billing & Subscription Management

**Current State**: None (internal use)  
**Required**: Usage-based billing, plans, invoicing

#### Pricing Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRICING TIERS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   STARTER ($10/user/month)                                      │
│   ├── Knowledge Hub (RAG)                                       │
│   ├── M365 Calendar integration                                 │
│   ├── Basic chat assistant                                      │
│   ├── 1,000 AI queries/user/month                               │
│   ├── Email support                                             │
│   └── 99% uptime SLA                                            │
│                                                                  │
│   PROFESSIONAL ($25/user/month)                                 │
│   ├── Everything in Starter                                     │
│   ├── Time Entry Assistant (Workday)                            │
│   ├── 1 premium connector included                              │
│   ├── 5,000 AI queries/user/month                               │
│   ├── Priority support (chat)                                   │
│   └── 99.5% uptime SLA                                          │
│                                                                  │
│   ENTERPRISE (Custom pricing)                                   │
│   ├── Everything in Professional                                │
│   ├── Unlimited connectors                                      │
│   ├── Unlimited AI queries                                      │
│   ├── Custom integrations                                       │
│   ├── Dedicated instance option                                 │
│   ├── SSO/SCIM provisioning                                     │
│   ├── Dedicated CSM                                             │
│   └── 99.9% uptime SLA                                          │
│                                                                  │
│   ADD-ONS                                                       │
│   ├── Additional AI queries: $0.01/query                        │
│   ├── Premium connector: $5/user/month each                     │
│   └── Knowledge Hub storage: $10/GB/month                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Stripe Integration

```python
# Billing service using Stripe
class BillingService:
    def __init__(self):
        stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    
    async def create_subscription(self, tenant_id: str, plan: str, seats: int):
        tenant = await self.get_tenant(tenant_id)
        
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=tenant.billing_email,
            name=tenant.name,
            metadata={"tenant_id": tenant_id}
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[
                {"price": PLAN_PRICES[plan], "quantity": seats}
            ],
            metadata={"tenant_id": tenant_id}
        )
        
        await self.update_tenant_subscription(tenant_id, subscription.id)
        return subscription

# Usage tracking
class UsageTracker:
    async def record_query(self, tenant_id: str, user_id: str, query_type: str):
        key = f"usage:{tenant_id}:{date.today().isoformat()}:queries"
        await self.redis.incr(key)
        await self.redis.expire(key, 60 * 60 * 24 * 35)  # 35 days TTL
    
    async def get_monthly_usage(self, tenant_id: str) -> UsageReport:
        month_start = date.today().replace(day=1)
        
        total_queries = 0
        current = month_start
        while current <= date.today():
            key = f"usage:{tenant_id}:{current.isoformat()}:queries"
            daily = await self.redis.get(key) or 0
            total_queries += int(daily)
            current += timedelta(days=1)
        
        return UsageReport(
            tenant_id=tenant_id,
            period=month_start,
            queries=total_queries,
            storage_gb=await self.measure_storage(tenant_id),
            active_users=await self.count_active_users(tenant_id)
        )
    
    async def report_usage_to_stripe(self, tenant_id: str):
        """Report metered usage to Stripe for billing."""
        usage = await self.get_monthly_usage(tenant_id)
        tenant = await self.get_tenant(tenant_id)
        
        # Report overage queries
        plan_limit = PLAN_QUERY_LIMITS[tenant.plan]
        overage = max(0, usage.queries - (plan_limit * tenant.seats))
        
        if overage > 0:
            stripe.SubscriptionItem.create_usage_record(
                tenant.stripe_item_id,
                quantity=overage,
                action="increment"
            )
```

---

### 6. Security Certifications

**Current State**: Internal security only  
**Required**: SOC 2 Type II, ISO 27001, GDPR

| Certification | Importance | Timeline | Estimated Cost |
|---------------|------------|----------|----------------|
| **SOC 2 Type II** | Critical for US enterprise | 6-12 months | $50-150K |
| **ISO 27001** | Important for global sales | 12-18 months | $30-80K |
| **GDPR Compliance** | Required for EU clients | Ongoing | Internal effort |
| **HIPAA** | Required for healthcare | 6-12 months | $30-100K |

#### Immediate Security Requirements

```python
# Audit logging for all data access
class AuditLogger:
    async def log_access(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: str,
        user_agent: str
    ):
        await self.db.execute(
            insert(AuditLog).values(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )
        )

# Data encryption at rest
class EncryptedStorage:
    def __init__(self, kms_key_id: str):
        self.kms = boto3.client('kms')
        self.key_id = kms_key_id
    
    def encrypt(self, data: bytes) -> bytes:
        response = self.kms.encrypt(KeyId=self.key_id, Plaintext=data)
        return response['CiphertextBlob']
    
    def decrypt(self, encrypted: bytes) -> bytes:
        response = self.kms.decrypt(CiphertextBlob=encrypted)
        return response['Plaintext']

# GDPR: Right to deletion
class GDPRService:
    async def delete_user_data(self, tenant_id: str, user_id: str):
        """Complete user data deletion per GDPR Article 17."""
        
        # 1. Delete from main database
        await self.db.execute(
            delete(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )
        
        # 2. Delete from Knowledge Hub
        await self.vector_db.delete_by_filter(
            namespace=f"tenant-{tenant_id}",
            filter={"created_by": user_id}
        )
        
        # 3. Delete from analytics
        await self.analytics.delete_user_events(user_id)
        
        # 4. Log deletion for compliance
        await self.audit_log("gdpr_deletion", tenant_id, user_id)
        
        return {"status": "deleted", "user_id": user_id}
```

---

### 7. Data Isolation & Residency

**Current State**: Single-region data  
**Required**: Tenant data isolation, multi-region options

```
DATA RESIDENCY OPTIONS
─────────────────────────────────────────────────────────────────

TENANT CONFIG:
  data_region: "us-east" | "eu-west" | "ap-southeast"
  
ROUTING:
  ├── US tenants    → Azure US East
  ├── EU tenants    → Azure West Europe (GDPR)
  └── APAC tenants  → Azure Singapore

ISOLATION:
  ├── Separate database schemas per tenant
  ├── Separate vector DB namespaces per tenant
  ├── Separate blob storage containers per tenant
  └── Tenant-specific encryption keys (Enterprise)
```

---

## Important Gaps (Address Before Scale)

### 8. Customer Admin Portal

```
┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER ADMIN PORTAL                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │ Dashboard   │  ← Usage, active users, costs, health         │
│  ├─────────────┤                                                │
│  │ Users       │  ← Invite, roles, deactivate, SCIM            │
│  ├─────────────┤                                                │
│  │ Connectors  │  ← Enable, configure credentials               │
│  ├─────────────┤                                                │
│  │ Branding    │  ← Logo, colors, custom domain                 │
│  ├─────────────┤                                                │
│  │ Security    │  ← SSO config, MFA policies, API keys          │
│  ├─────────────┤                                                │
│  │ Billing     │  ← Plan, invoices, payment methods             │
│  ├─────────────┤                                                │
│  │ Audit Logs  │  ← Who did what when                          │
│  ├─────────────┤                                                │
│  │ Support     │  ← Tickets, docs, contact                      │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9. Public API for Customers

```python
# Public API for customer integrations
@router.get("/api/v1/public/users")
async def list_users(request: Request, api_key: str = Header(..., alias="X-API-Key")):
    tenant_id = await verify_api_key(api_key)
    return await get_tenant_users(tenant_id)

@router.post("/api/v1/public/knowledge/ingest")
async def ingest_document(
    request: Request,
    file: UploadFile,
    api_key: str = Header(..., alias="X-API-Key")
):
    tenant_id = await verify_api_key(api_key)
    return await knowledge_service.ingest_document(tenant_id, file)

# Webhook subscriptions
@router.post("/api/v1/public/webhooks")
async def register_webhook(config: WebhookConfig, api_key: str = Header(...)):
    """Allow customers to subscribe to events."""
    tenant_id = await verify_api_key(api_key)
    return await create_webhook(tenant_id, config)
```

### 10. SLA & Support Infrastructure

| Tier | Response Time | Uptime SLA | Support Channels |
|------|---------------|------------|------------------|
| Starter | 48 hours | 99% | Email, Docs |
| Professional | 8 hours | 99.5% | Email, Chat |
| Enterprise | 1 hour | 99.9% | Phone, Dedicated CSM |

**Required Infrastructure**:
- Help desk system (Zendesk, Intercom)
- Status page (status.opsiq.ai)
- Runbook documentation
- On-call rotation
- Incident management process

---

## Nice-to-Have Gaps (Competitive Advantage)

### 11. Analytics & Insights for Customers

```
CUSTOMER ANALYTICS DASHBOARD
─────────────────────────────────────────
• Time saved per user per week
• Most used connectors
• Knowledge Hub query trends
• Adoption metrics by department
• ROI calculator with real data
• Benchmark comparisons vs. peers
```

### 12. AI Model Customization per Tenant

```
TENANT-SPECIFIC AI
─────────────────────────────────────────
• Custom system prompts per tenant
• Tenant-specific fine-tuning data
• Learning from tenant usage patterns
• Custom entity extraction (client names, project codes)
• Tenant-specific response styles
```

### 13. Marketplace for Templates

```
TEMPLATE MARKETPLACE
─────────────────────────────────────────
• Pre-built workflow templates
• Industry-specific knowledge packs (Audit, Tax, Advisory)
• Onboarding templates for new hires
• Integration playbooks
• Prompt libraries
```

---

## Business Model

### Pricing Strategy

| Model | Description | Fit |
|-------|-------------|-----|
| **Per-seat subscription** | Base fee per user per month | ✅ Primary revenue |
| **Usage-based** | Charge for AI query overages | ✅ Scales with value |
| **Per-connector** | Premium integrations as add-ons | ✅ Upsell path |
| **Revenue share** | Partner connector sales | ⚠️ Future platform |

### Unit Economics Target

| Metric | Target |
|--------|--------|
| CAC (Customer Acquisition Cost) | < $5,000 |
| ACV (Annual Contract Value) | $10,000 - $50,000 |
| LTV (Lifetime Value) | > $50,000 |
| LTV:CAC Ratio | > 3:1 |
| Gross Margin | > 70% |
| Net Revenue Retention | > 110% |

---

## Productization Roadmap

| Phase | Timeline | Focus | Outcome |
|-------|----------|-------|---------|
| **Phase 1: Foundation** | Months 0-3 | Multi-tenancy, data isolation, basic billing | Ready for 2-3 beta customers |
| **Phase 2: Self-Service** | Months 3-6 | Onboarding wizard, admin portal, connector config | Scalable sales motion |
| **Phase 3: Enterprise** | Months 6-12 | SOC 2, SSO/SCIM, SLA, dedicated support | Enterprise deals possible |
| **Phase 4: Platform** | Months 12-18 | Partner API, marketplace, regional deployment | Platform ecosystem |

---

## Immediate Next Steps

| # | Action | Owner | Timeline | Notes |
|---|--------|-------|----------|-------|
| 1 | Add `tenant_id` column to all database tables | Engineering | Week 1-2 | Non-breaking migration |
| 2 | Create tenant isolation middleware | Engineering | Week 2-3 | Request-scoped tenant |
| 3 | Design branding configuration schema | Product | Week 1 | White-label requirements |
| 4 | Set up Stripe integration skeleton | Engineering | Week 3-4 | Test mode first |
| 5 | Create admin portal wireframes | Design | Week 2-3 | MVP scope |
| 6 | Draft data processing agreement (DPA) | Legal | Week 1-2 | GDPR requirement |
| 7 | Define pricing tiers and limits | Product/Finance | Week 2 | Competitive analysis |
| 8 | Identify 2-3 beta customers | Sales/Partnerships | Ongoing | Friendly firms |
| 9 | Create SOC 2 readiness checklist | Security | Week 3-4 | Gap assessment |
| 10 | Build tenant provisioning automation | Engineering | Week 4-6 | Self-service goal |

---

## Key Insight

> The **modular architecture** already built (MCP servers, pluggable integrations, Tauri desktop) is **exactly right** for productization. The main work is adding the **SaaS wrapper** (multi-tenancy, billing, admin portal) around the existing core.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Competitor entry** | Medium | High | Move fast, lock in early customers |
| **Security incident** | Low | Critical | SOC 2, security-first design |
| **Connector complexity** | Medium | Medium | Prioritize top 3-5 integrations |
| **Support burden** | High | Medium | Self-service tools, docs |
| **Pricing wrong** | Medium | Medium | Start high, discount down |
| **Integration fragility** | Medium | High | Robust error handling, retry logic |

---

## Competitive Landscape

| Competitor | Strengths | Weaknesses | Our Advantage |
|------------|-----------|------------|---------------|
| **Generic AI assistants** | Brand, scale | No integrations | Deep professional services focus |
| **Workday add-ons** | Native integration | Single-purpose | Multi-system orchestration |
| **ServiceNow AI** | Enterprise presence | Expensive, complex | Lightweight, fast deployment |
| **Custom builds** | Tailored exactly | Expensive, slow | Productized, proven |

---

## Success Criteria for First External Customer

- [ ] Complete tenant isolation verified
- [ ] Customer can self-configure branding
- [ ] At least 2 connectors configurable by customer
- [ ] Billing operational (even if manual)
- [ ] Basic admin portal functional
- [ ] SLA and support process defined
- [ ] Data processing agreement signed
- [ ] Security questionnaire completed

---

## Team Structure & Resourcing

### Phase 1: Internal Rollout Team (3-6 months)

| Role | FTE | Internal/External | Focus |
|------|-----|-------------------|-------|
| **Product Owner** | 1 | Internal | Prioritization, stakeholder alignment, rollout strategy |
| **Senior Full-Stack Engineer** | 1-2 | Internal or Contract | Feature completion, bug fixes, technical debt |
| **DevOps/Platform Engineer** | 1 | Internal or Contract | CI/CD, Azure Container Apps, monitoring (DataDog) |
| **QA/Test Engineer** | 0.5-1 | Internal or Contract | E2E testing, regression, UAT coordination |
| **Security/Compliance Lead** | 0.5 | Internal | Presidio tuning, audit trails, SOC 2 prep |
| **Change Management/Training** | 0.5-1 | Internal | User onboarding, documentation, feedback loops |

**Total:** ~5-7 people (mix of dedicated + part-time)

### Phase 2: Productization Team (6-18 months)

#### Core Engineering
| Role | FTE | Notes |
|------|-----|-------|
| **Engineering Manager** | 1 | Coordinates across pods |
| **Backend Engineers** | 2-3 | Multi-tenancy, billing integration, API hardening |
| **Frontend Engineers** | 1-2 | White-label theming, onboarding flows |
| **Platform/Infra Engineer** | 1-2 | Kubernetes/ACA scaling, tenant isolation, DR |
| **Data Engineer** | 1 | RAG pipeline optimization, Weaviate scaling |

#### Product & Design
| Role | FTE | Notes |
|------|-----|-------|
| **Product Manager** | 1 | Roadmap, pricing tiers, competitive positioning |
| **UX Designer** | 0.5-1 | Onboarding, self-service portal, white-label |

#### Security & Compliance
| Role | FTE | Notes |
|------|-----|-------|
| **Security Engineer** | 1 | Pen testing, SOC 2 Type II, data isolation |
| **Compliance/Legal** | 0.5 | DPA, BAA (if healthcare), contract templates |

#### Go-to-Market
| Role | FTE | Notes |
|------|-----|-------|
| **Customer Success** | 1-2 | Onboarding, support, renewals |
| **Solutions Architect** | 0.5-1 | Pre-sales, custom integrations |
| **Marketing** | 0.5 | Positioning, content, demos |

#### External Partners
| Partner Type | Purpose |
|--------------|---------|
| **Managed Security Provider** | SOC 2 audit, pen testing |
| **Legal Counsel** | SaaS contracts, data privacy |
| **Azure/Cloud Partner** | Reserved instances, architecture review |
| **Implementation Partner** | Customer-specific integrations |

**Total Productization Team:** ~12-18 people + external partners

---

## AI-Augmented Development Strategy

> **Reference:** See [ai_augmented_development.md](./ai_augmented_development.md) for detailed guidelines.

### The Multiplier Effect

AI coding assistants (Antigravity Ultra, GitHub Copilot) dramatically accelerate development:

| Work Category | Traditional Dev | With AI Pair (Ultra Tier) | Multiplier |
|---------------|-----------------|---------------------------|------------|
| **Scaffolding & Boilerplate** | 2-3 days | 2-3 hours | **10-15x** |
| **Integration Code** (D365, ServiceNow, Workday) | 1-2 weeks each | 1-2 days each | **5-7x** |
| **Debugging & Fixing** | Varies | ~50% faster with context | **2x** |
| **Documentation** | Often skipped | Generated inline | **∞** |
| **Architecture Decisions** | Days of research | Minutes with guided reasoning | **5-10x** |
| **Refactoring** | High risk, slow | Rapid with confidence | **3-5x** |

**Overall Velocity:** An engineer with Ultra-tier AI assistance operates at roughly **2.5-4x** the velocity of a traditional developer for greenfield and integration-heavy work.

### Cost-Benefit Analysis

#### Scenario: 3 Engineers with Ultra Tier

| Metric | Without AI | With AI (Ultra) |
|--------|------------|-----------------|
| **Team Size Needed** | 5-6 engineers | 3 engineers |
| **Time to Internal Rollout** | 6 months | 2-3 months |
| **Time to Productization** | 18 months | 8-12 months |
| **AI Tooling Cost** | $0 | ~$60-100/seat/month |
| **Salary Savings** | - | 2-3 FTEs × $150K = **$300-450K/year** |

#### ROI Calculation
```
AI Cost:        3 seats × $100/mo × 12 = $3,600/year
Salary Savings: 2 FTEs × $150K = $300,000/year
───────────────────────────────────────────────────
Net Savings:    ~$296,400/year
ROI:            8,200%+
```

### Revised Team Structure with AI Augmentation

| Phase | Traditional | AI-Augmented |
|-------|-------------|--------------|
| **Phase 1 (Internal)** | 5-7 people | **3-4 people** |
| **Phase 2 (Productize)** | 12-18 people | **7-10 people** |

### Phased Hiring Recommendation

```
Phase 1 (Internal Rollout)     Phase 2a (Foundation)      Phase 2b (Scale)
─────────────────────────────  ─────────────────────────  ──────────────────
You + AI (current)             +Product Manager           +2 Backend Eng
+1 DevOps (contract)           +1 Backend Engineer        +Security Engineer
+1 Full-Stack (contract)       +1 Platform Engineer       +Customer Success
+0.5 QA                        +0.5 UX Designer           +Solutions Architect
                               +Security Consultant       +Marketing
```

### The New Hiring Bar

Instead of "Can you build X?", the question becomes:
> **"Can you effectively direct AI to build X, review its output, and catch edge cases?"**

### Key Recommendations

| Action | Timing |
|--------|--------|
| Give **all engineers** Ultra-tier AI access | Immediately |
| Hire **fewer engineers, more senior** | Phase 1 |
| Add **AI-fluent contractors** for burst capacity | As needed |
| Invest in **prompt engineering training** | First 2 weeks |
| Establish **AI code review guidelines** | Before production |

---

## Summary: Time & Resource Savings

| Metric | Traditional Approach | AI-Augmented Approach |
|--------|---------------------|----------------------|
| **Time to Market** | 18-24 months | **8-12 months** |
| **Team Size** | 12-18 people | **7-10 people** |
| **Total Investment** | $2-3M | **$1-1.5M** |
| **Documentation Quality** | Inconsistent | **Comprehensive** |
| **Technical Debt** | Higher | **Lower** (AI enforces patterns) |
