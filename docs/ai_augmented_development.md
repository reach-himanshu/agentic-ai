# AI-Augmented Development Guidelines

> **Purpose:** Establish best practices for leveraging AI coding assistants (Antigravity, Copilot, Cursor) to maximize productivity while maintaining code quality, security, and compliance.

---

## 🎯 Philosophy

**AI is a force multiplier, not a replacement.**

Our engineers use AI to:
- Accelerate routine and boilerplate work
- Explore solutions faster through rapid prototyping
- Maintain comprehensive documentation
- Catch bugs earlier through AI-assisted review

Our engineers remain responsible for:
- Architectural decisions
- Security and compliance validation
- Business logic correctness
- Final code approval

---

## 📊 Expected Productivity Gains

| Work Category | Traditional | AI-Augmented | Your Role |
|---------------|-------------|--------------|-----------|
| Scaffolding & Boilerplate | Days | Hours | Review & customize |
| API Integrations | Weeks | Days | Validate auth & error handling |
| Bug Fixing | Hours-Days | Minutes-Hours | Verify root cause |
| Documentation | Often skipped | Inline | Review for accuracy |
| Refactoring | High risk | Guided & safe | Approve scope |
| Test Generation | Tedious | Automated | Review coverage |

---

## 🚀 Getting Started

### Tool Access
All engineers receive **Ultra-tier access** to AI coding assistants. Current approved tools:
- **Antigravity** (Primary) – Full agentic capabilities
- **GitHub Copilot** (Secondary) – Inline completions
- **Claude/ChatGPT** (Research) – Architecture discussions

### Day 1 Setup
1. Install approved AI tools in your IDE
2. Complete the **AI Pair Programming Onboarding** (2 hours)
3. Review this document and the security guidelines below
4. Shadow an experienced AI-augmented developer for first session

---

## 💡 Effective AI Collaboration

### The DIRECT Framework

| Step | Description | Example |
|------|-------------|---------|
| **D**efine | State the goal clearly | "Create a FastAPI endpoint for..." |
| **I**nput | Provide context (files, patterns) | "Following the pattern in auth.py..." |
| **R**estrict | Set boundaries | "Do not modify existing tests" |
| **E**xecute | Let AI generate | Review the proposed changes |
| **C**ritique | Review critically | Check edge cases, security |
| **T**est | Validate the output | Run tests, manual verification |

### Prompting Best Practices

#### ✅ Do
```markdown
"Create a new MCP tool for fetching ServiceNow incidents.
Follow the pattern in iis/mcp_registry/d365.py.
Include error handling for 401 and 404 responses.
Add docstrings and type hints."
```

#### ❌ Don't
```markdown
"Make a ServiceNow thing"
```

### Context is King
- **Open relevant files** before asking AI to modify code
- **Reference existing patterns** ("like we did in X")
- **Share error messages** completely, not summarized
- **Explain the business context** when logic is domain-specific

---

## 🔒 Security Guidelines

### NEVER Let AI Handle Directly

| Category | Requirement |
|----------|-------------|
| **Secrets & Credentials** | Never paste API keys, passwords, or tokens |
| **PII/PHI Data** | Never use real customer data in prompts |
| **Auth Logic** | Always human-review authentication flows |
| **Data Isolation** | Multi-tenant queries require human approval |
| **Financial Calculations** | Billing/invoicing logic needs manual verification |

### Mandatory Human Review

The following changes require **explicit human review** before merge:

```yaml
Security-Critical Paths:
  - iis/core/auth.py
  - iis/core/identity.py
  - iis/middleware/security/
  - Any file containing "token", "secret", "password", "key"

Data Access Paths:
  - iis/integrations/*/
  - iis/core/db/
  - Any SQL or ORM query modifications

Infrastructure:
  - Dockerfile, docker-compose.yml
  - Azure Bicep/ARM templates
  - CI/CD pipeline definitions
```

### AI-Generated Code Review Checklist

Before approving AI-generated code, verify:

- [ ] **No hardcoded secrets** – Environment variables only
- [ ] **Proper error handling** – No swallowed exceptions
- [ ] **Input validation** – All user inputs sanitized
- [ ] **Logging** – Sensitive data not logged
- [ ] **SQL injection** – Parameterized queries only
- [ ] **Auth checks** – Proper authorization on all endpoints
- [ ] **Tests included** – AI should generate tests with code

---

## 🔄 Development Workflow

### AI-Augmented Git Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  1. Create Branch                                                │
│     └─ git checkout -b feature/my-feature                       │
├──────────────────────────────────────────────────────────────────┤
│  2. AI Development Session                                       │
│     └─ Use AI to scaffold, implement, test                      │
│     └─ Commit frequently with descriptive messages              │
├──────────────────────────────────────────────────────────────────┤
│  3. Self-Review                                                  │
│     └─ Read EVERY line AI generated                             │
│     └─ Run security checklist above                             │
├──────────────────────────────────────────────────────────────────┤
│  4. AI-Assisted PR Description                                   │
│     └─ Ask AI to summarize changes                              │
│     └─ Include "AI-Assisted: Yes" label                         │
├──────────────────────────────────────────────────────────────────┤
│  5. Human Code Review                                            │
│     └─ Reviewer focuses on logic, security, edge cases          │
│     └─ AI handles style/formatting (via linters)                │
├──────────────────────────────────────────────────────────────────┤
│  6. Merge & Deploy                                               │
│     └─ Standard CI/CD pipeline                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Commit Message Convention

```
feat(component): Brief description

AI-Assisted: Yes/No
Human-Reviewed: [Your Name]

- Detail 1
- Detail 2
```

---

## 📋 Use Case Playbooks

### 1. New API Integration

```markdown
Prompt Template:
"Create a new integration for [SERVICE] in iis/integrations/[service]/.
Follow the pattern established in iis/integrations/d365/.
Include:
- OAuth 2.0 client credentials flow
- Retry logic with exponential backoff
- Proper error handling and logging
- Unit tests with mocked responses
- MCP tool registration in iis/mcp_registry/"
```

### 2. Frontend Component

```markdown
Prompt Template:
"Create a new React component for [FEATURE].
Follow the design system in frontend/src/components/.
Include:
- TypeScript interfaces
- Dark/light theme support
- Loading and error states
- Responsive design
- Storybook story (if applicable)"
```

### 3. Bug Fix

```markdown
Prompt Template:
"Debug the following error: [PASTE FULL ERROR]
Context:
- File: [path]
- Expected behavior: [description]
- Actual behavior: [description]
- Steps to reproduce: [steps]

Identify the root cause and propose a fix."
```

### 4. Documentation

```markdown
Prompt Template:
"Generate documentation for [FILE/MODULE].
Include:
- Purpose and overview
- Usage examples
- API reference (if applicable)
- Configuration options
- Troubleshooting common issues"
```

---

## 📈 Measuring Success

### Team Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Velocity Increase** | 2-3x | Story points per sprint |
| **Time to First PR** | < 2 hours | New feature kickoff to PR |
| **Documentation Coverage** | 100% | All public APIs documented |
| **Test Coverage** | > 80% | AI-generated tests included |
| **Security Incidents** | 0 | Post-deployment issues |

### Individual KPIs

| Indicator | Green | Yellow | Red |
|-----------|-------|--------|-----|
| AI adoption | Daily use | Weekly use | Rarely |
| Self-review | Always | Sometimes | Never |
| Prompt quality | Detailed | Basic | Vague |
| Security awareness | Proactive | Reactive | Negligent |

---

## 🎓 Training & Resources

### Required Training (Week 1)
- [ ] AI Pair Programming Fundamentals (2 hours)
- [ ] Security-Aware AI Development (1 hour)
- [ ] Codebase Pattern Library Review (1 hour)

### Recommended Learning
- Prompt Engineering Best Practices
- AI Code Review Techniques
- Effective Human-AI Collaboration

### Internal Resources
- `docs/system_architecture.md` – Understand the stack
- `docs/productization_strategy.md` – Business context
- `.agent/workflows/` – Automated workflow patterns

---

## ⚠️ Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Blind Trust** | Accepting AI output without review | Always read every line |
| **Prompt Laziness** | Vague, context-free prompts | Use DIRECT framework |
| **Secret Leakage** | Pasting credentials in prompts | Use environment variables |
| **Over-Reliance** | Can't code without AI | Maintain fundamental skills |
| **Skipping Tests** | "AI wrote it, it's fine" | AI must generate tests too |
| **Ignoring Warnings** | Dismissing AI security suggestions | Investigate all warnings |

---

## 🔄 Continuous Improvement

### Weekly AI Retrospective (15 min)
- What AI-assisted tasks went well?
- Where did AI output need significant correction?
- Any new patterns to add to playbooks?

### Monthly Review
- Update this document with lessons learned
- Share successful prompt patterns
- Identify training needs

---

## 📞 Support

| Issue | Contact |
|-------|---------|
| AI tool access | IT Helpdesk |
| Security concerns | Security Team |
| Best practices questions | Tech Lead |
| Billing/licensing | Operations |

---

> **Remember:** AI makes you faster, not infallible. The goal is to ship better software, faster – while maintaining the quality and security our customers expect.

---

*Last Updated: January 2026*
*Owner: Engineering Team*
*Review Cycle: Quarterly*
