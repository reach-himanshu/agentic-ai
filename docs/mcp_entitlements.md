# MCP Entitlements & Access Control

## Overview

This document describes the entitlement architecture for controlling which users can access which MCP servers and tools within Ops IQ.

---

## Problem Statement

Different user groups need access to different integrations and capabilities:

| User Group | MCP Servers | Tool Restrictions |
|------------|-------------|-------------------|
| G1: IT Support | ServiceNow, Knowledge Hub | Can create but not delete tickets |
| G2: Finance | D365, Knowledge Hub | Can create but not approve large invoices |
| G3: Managers | All MCPs | Full access to their department's tools |

---

## Entitlement Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTITLEMENT LAYERS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   LAYER 1: MCP SERVER ACCESS                                    │
│   ──────────────────────────────────────────────────────────────│
│   "Which integrations can this user see?"                       │
│                                                                  │
│   IT Support Users      │  Finance Users                        │
│   ├── ServiceNow ✅      │  ├── ServiceNow ❌                    │
│   ├── D365 ❌            │  ├── D365 ✅                          │
│   └── Knowledge Hub ✅   │  └── Knowledge Hub ✅                 │
│                                                                  │
│   LAYER 2: TOOL ACCESS (within each MCP)                        │
│   ──────────────────────────────────────────────────────────────│
│   "Which tools/actions within an integration can they use?"     │
│                                                                  │
│   ServiceNow MCP:                                               │
│   ├── list_tickets ✅ (all users)                               │
│   ├── create_ticket ✅ (all users)                              │
│   ├── close_ticket ⚠️ (managers only)                           │
│   └── delete_ticket ❌ (admins only)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture: Hybrid RBAC + Entra Sync

```
┌─────────────────────────────────────────────────────────────────┐
│                 RECOMMENDED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ENTRA ID                          OPS IQ BACKEND              │
│   ─────────────────                 ─────────────────           │
│   ┌─────────────────┐               ┌─────────────────┐         │
│   │ User: john.doe  │               │ ENTITLEMENT DB  │         │
│   │ Groups:         │──── sync ────→│                 │         │
│   │ • IT-Support    │               │ Roles:          │         │
│   │ • ServiceNow-   │               │ • IT-Support    │         │
│   │   Users         │               │   └─ mcp:sn:*   │         │
│   └─────────────────┘               │   └─ mcp:kb:r   │         │
│                                     │ • Finance-User  │         │
│                                     │   └─ mcp:d365:* │         │
│                                     │   └─ mcp:kb:r   │         │
│                                     └─────────────────┘         │
│                                             │                   │
│                                             ▼                   │
│                                     ┌─────────────────┐         │
│                                     │ CAPABILITY      │         │
│                                     │ FILTER          │         │
│                                     │                 │         │
│                                     │ 1. Get user role│         │
│                                     │ 2. Get allowed  │         │
│                                     │    MCP + tools  │         │
│                                     │ 3. Filter agent │         │
│                                     │    capabilities │         │
│                                     └─────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```python
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)      # "IT-Support", "Finance-User"
    description = Column(String)
    entra_group_id = Column(String)         # Sync from Entra group

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    resource = Column(String)               # "mcp:servicenow", "mcp:d365"
    action = Column(String)                 # "read", "create_ticket", "*"

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)

class UserEntitlement(Base):
    __tablename__ = "user_entitlements"
    
    user_id = Column(String, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    additional_permissions = Column(JSON, default=[])  # User-specific overrides
    denied_permissions = Column(JSON, default=[])      # User-specific denials
```

---

## Permission Definitions

```python
MCP_PERMISSIONS = {
    "servicenow": {
        "list_tickets": "mcp:servicenow:list_tickets",
        "get_ticket": "mcp:servicenow:get_ticket",
        "create_ticket": "mcp:servicenow:create_ticket",
        "update_ticket": "mcp:servicenow:update_ticket",
        "close_ticket": "mcp:servicenow:close_ticket",
        "delete_ticket": "mcp:servicenow:delete_ticket",
    },
    "d365": {
        "list_accounts": "mcp:d365:list_accounts",
        "get_account": "mcp:d365:get_account",
        "create_invoice": "mcp:d365:create_invoice",
        "approve_invoice": "mcp:d365:approve_invoice",
    },
    "knowledge_hub": {
        "search": "mcp:knowledge:search",
        "read_document": "mcp:knowledge:read",
        "ingest_document": "mcp:knowledge:ingest",
        "delete_document": "mcp:knowledge:delete",
    }
}

ROLE_DEFINITIONS = {
    "IT-Support": [
        "mcp:servicenow:list_tickets",
        "mcp:servicenow:get_ticket",
        "mcp:servicenow:create_ticket",
        "mcp:servicenow:update_ticket",
        "mcp:knowledge:search",
        "mcp:knowledge:read",
    ],
    "IT-Manager": [
        "mcp:servicenow:*",      # All ServiceNow tools
        "mcp:knowledge:*",       # All Knowledge tools
    ],
    "Finance-User": [
        "mcp:d365:list_accounts",
        "mcp:d365:get_account",
        "mcp:d365:create_invoice",
        "mcp:knowledge:search",
        "mcp:knowledge:read",
    ],
    "Finance-Manager": [
        "mcp:d365:*",
        "mcp:knowledge:*",
    ],
}
```

---

## Entitlement Service

```python
class EntitlementService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_permissions(self, user_id: str) -> set[str]:
        """Get all permissions for a user."""
        roles = await self.db.execute(
            select(Role)
            .join(UserEntitlement)
            .where(UserEntitlement.user_id == user_id)
        )
        
        permissions = set()
        for role in roles.scalars():
            role_perms = ROLE_DEFINITIONS.get(role.name, [])
            permissions.update(role_perms)
        
        return permissions
    
    def can_access_mcp(self, permissions: set[str], mcp_name: str) -> bool:
        """Check if user can access an MCP server."""
        prefix = f"mcp:{mcp_name}:"
        return any(
            p.startswith(prefix) or p == f"mcp:{mcp_name}:*"
            for p in permissions
        )
    
    def can_use_tool(self, permissions: set[str], mcp_name: str, tool_name: str) -> bool:
        """Check if user can use a specific tool."""
        required = f"mcp:{mcp_name}:{tool_name}"
        wildcard = f"mcp:{mcp_name}:*"
        return required in permissions or wildcard in permissions
    
    def get_available_mcps(self, permissions: set[str]) -> list[str]:
        """Get list of MCPs user can access."""
        available = []
        for mcp in ["servicenow", "d365", "knowledge_hub"]:
            if self.can_access_mcp(permissions, mcp):
                available.append(mcp)
        return available
    
    def filter_tools(self, permissions: set[str], mcp_name: str, tools: list[dict]) -> list[dict]:
        """Filter tool list to only those user can access."""
        return [
            tool for tool in tools
            if self.can_use_tool(permissions, mcp_name, tool["name"])
        ]
```

---

## Integration with PlannerAgent

```python
class PlannerAgent:
    def __init__(self, user_id: str, entitlements: EntitlementService):
        self.user_id = user_id
        self.entitlements = entitlements
    
    async def initialize(self):
        """Load user permissions on agent start."""
        self.permissions = await self.entitlements.get_user_permissions(self.user_id)
        
        # Filter available MCP servers
        available_mcps = self.entitlements.get_available_mcps(self.permissions)
        
        # Only initialize allowed MCP clients
        self.mcp_clients = {}
        if "servicenow" in available_mcps:
            self.mcp_clients["servicenow"] = ServiceNowMCP()
        if "d365" in available_mcps:
            self.mcp_clients["d365"] = D365MCP()
        if "knowledge_hub" in available_mcps:
            self.mcp_clients["knowledge_hub"] = KnowledgeHubMCP()
    
    async def execute_tool(self, mcp_name: str, tool_name: str, params: dict):
        """Execute a tool with permission check."""
        if not self.entitlements.can_use_tool(self.permissions, mcp_name, tool_name):
            raise PermissionError(f"Not authorized to use {mcp_name}:{tool_name}")
        
        return await self.mcp_clients[mcp_name].call_tool(tool_name, params)
```

---

## API Endpoints

### Get User Capabilities

```python
@app.get("/api/v1/capabilities")
async def get_user_capabilities(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available MCPs and tools for current user."""
    entitlements = EntitlementService(db)
    permissions = await entitlements.get_user_permissions(user.id)
    
    capabilities = {}
    for mcp_name in entitlements.get_available_mcps(permissions):
        mcp_tools = MCP_PERMISSIONS.get(mcp_name, {})
        available_tools = [
            tool_name for tool_name in mcp_tools.keys()
            if entitlements.can_use_tool(permissions, mcp_name, tool_name)
        ]
        capabilities[mcp_name] = available_tools
    
    return {"capabilities": capabilities}

# Example response for IT-Support user:
# {
#   "capabilities": {
#     "servicenow": ["list_tickets", "get_ticket", "create_ticket", "update_ticket"],
#     "knowledge_hub": ["search", "read_document"]
#   }
# }
```

### Admin: Manage Roles

```python
@app.post("/api/v1/admin/roles/{role_name}/permissions")
async def set_role_permissions(role_name: str, permissions: list[str]):
    """Set permissions for a role."""
    pass

@app.post("/api/v1/admin/users/{user_id}/roles")
async def assign_user_role(user_id: str, role_name: str):
    """Assign a role to a user."""
    pass

@app.get("/api/v1/admin/roles")
async def list_roles():
    """List all roles and their permissions."""
    pass
```

---

## Frontend: Dynamic UI

```typescript
// src/hooks/useCapabilities.ts
export function useCapabilities() {
  const [capabilities, setCapabilities] = useState<Record<string, string[]>>({});
  
  useEffect(() => {
    fetch('/api/v1/capabilities')
      .then(res => res.json())
      .then(data => setCapabilities(data.capabilities));
  }, []);
  
  const canAccessMcp = (mcp: string) => mcp in capabilities;
  const canUseTool = (mcp: string, tool: string) => 
    capabilities[mcp]?.includes(tool) ?? false;
  
  return { capabilities, canAccessMcp, canUseTool };
}

// Usage in component
function ChatInterface() {
  const { canAccessMcp, canUseTool } = useCapabilities();
  
  return (
    <div>
      {canAccessMcp('servicenow') && <ServiceNowPanel />}
      {canAccessMcp('d365') && <D365Panel />}
      
      {canUseTool('servicenow', 'create_ticket') && (
        <button>Create Ticket</button>
      )}
    </div>
  );
}
```

---

## Entra ID Group Sync

```python
async def sync_user_roles_from_entra(user_id: str, access_token: str):
    """Sync user's Entra groups to local roles."""
    # Get user's group memberships from Graph API
    groups = await get_user_groups(access_token)
    
    # Map Entra groups to local roles
    GROUP_TO_ROLE = {
        "IT-Support-Team": "IT-Support",
        "IT-Managers": "IT-Manager",
        "Finance-Department": "Finance-User",
        "Finance-Leadership": "Finance-Manager",
    }
    
    user_roles = []
    for group in groups:
        if group["displayName"] in GROUP_TO_ROLE:
            user_roles.append(GROUP_TO_ROLE[group["displayName"]])
    
    # Update local entitlements
    await update_user_entitlements(user_id, user_roles)
```

---

## Targeting Options

### Option 1: Group-Based (Simple)

Users assigned to Entra groups automatically get corresponding roles.

```
Entra Group "IT-Support-Team" → Role "IT-Support" → Permissions [mcp:sn:*, mcp:kb:r]
```

### Option 2: Hand-Picked (Explicit)

Admin explicitly assigns roles to specific users.

```python
POST /api/v1/admin/users/john.doe/roles
{ "role": "IT-Manager" }
```

### Option 3: Attribute-Based (ABAC)

Dynamic rules based on user attributes.

```python
RULES = [
    {"if": {"department": "IT"}, "grant": ["mcp:servicenow:*"]},
    {"if": {"department": "Finance", "level": "Manager"}, "grant": ["mcp:d365:*"]},
]
```

---

## Example Configurations

### IT Support Team

| Permission | Allowed |
|------------|---------|
| ServiceNow: List tickets | ✅ |
| ServiceNow: Create ticket | ✅ |
| ServiceNow: Delete ticket | ❌ |
| D365: All | ❌ |
| Knowledge Hub: Search | ✅ |
| Knowledge Hub: Delete | ❌ |

### Finance Team

| Permission | Allowed |
|------------|---------|
| ServiceNow: All | ❌ |
| D365: List accounts | ✅ |
| D365: Create invoice | ✅ |
| D365: Approve invoice | ❌ (managers only) |
| Knowledge Hub: Search | ✅ |
| Knowledge Hub: Delete | ❌ |

---

## Summary

| Approach | Complexity | Flexibility | Use Case |
|----------|------------|-------------|----------|
| Group-Based | Low | Low | MVP, simple orgs |
| RBAC | Medium | Medium | **Recommended** |
| ABAC | High | High | Complex policies |

| Layer | What It Controls | Implementation |
|-------|------------------|----------------|
| MCP Server Access | Which integrations user sees | Role → MCP mapping |
| Tool Access | Which actions within MCP | Permission strings |
| Data Access | What data within tool | ABAC policies (future) |
