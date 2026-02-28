# Intelligent Time Entry Assistant

## Executive Summary

The Time Entry Assistant is a high-value feature for Ops IQ that transforms the tedious weekly timesheet process into an intelligent, friction-free experience. By leveraging calendar data, Workday project information, and local caching, the assistant pre-drafts time entries, nudges users for review, and allows flexible submission.

---

## Problem Statement

### The Pain Points

| Pain Point | Impact | Frequency |
|------------|--------|-----------|
| **Time entry is tedious** | 15-30 min/week wasted | Daily |
| **Retrospective entry** | Inaccurate billable hours | Weekly |
| **Project code hunting** | Friction, wrong codes selected | Every entry |
| **Missed billable time** | **Revenue leakage (5-15%)** | Ongoing |
| **Compliance pressure** | Friday afternoon stress | Weekly |
| **No offline capability** | Can't log time on the go | Situational |

### Market Validation

> "Professionals at consulting firms spend an average of **6.3 hours/month** on time entry, with **10-15% of billable time** going unreported."

### ROI Calculation

```
Professional Services Firm (500 consultants)
───────────────────────────────────────────
Average billing rate: $200/hour
Hours recovered per person/week: 1.5 hours
Weekly recovered revenue: 500 × 1.5 × $200 = $150,000
Annual impact: $7.8M recovered billable revenue

Development cost: ~$200K
ROI: 39x in year one
```

---

## Product Manager Perspective

### Value Proposition

```
┌─────────────────────────────────────────────────────────────────┐
│                    VALUE PROPOSITION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   BEFORE: "I dread Friday afternoon time entry"                 │
│   ──────────────────────────────────────────────────────────────│
│   • Open Workday → Search project → Remember hours → Enter      │
│   • 30 clicks per day × 5 days = 150 clicks/week                │
│   • Forgotten meetings = lost revenue                           │
│                                                                  │
│   AFTER: "Ops IQ drafts my timesheet for me"                    │
│   ──────────────────────────────────────────────────────────────│
│   • AI pre-drafts based on calendar + tasks                     │
│   • 2-click approval: "Looks good" → Submit                     │
│   • Nudge on Friday: "Your draft is ready for review"           │
│   • Save locally, submit whenever convenient                    │
│   • **Zero forgotten hours**                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Success Metrics

| Metric | Baseline | Target | Value |
|--------|----------|--------|-------|
| Time to complete weekly entry | 25 min | < 5 min | **80% reduction** |
| Billable hours captured | 85% | 98% | **+15% revenue** |
| User satisfaction (NPS) | N/A | > 50 | Adoption driver |
| Friday late entries | 60% | < 20% | Compliance |
| Offline time logging | 0% | 100% | Flexibility |

### Key Differentiators

| Feature | Traditional Time Entry | Ops IQ Assistant |
|---------|------------------------|------------------|
| Data entry | Manual recall | AI pre-drafts from calendar |
| Project search | Slow, clunky | Instant local cache |
| Submit timing | Must be online | Save locally, submit later |
| Reminders | None or email | Smart push notifications |
| Voice input | None | "Log 2 hours for Acme" |

---

## User Perspective

### Current Experience (Pain)

```
┌─────────────────────────────────────────────────────────────────┐
│                 CURRENT TIME ENTRY EXPERIENCE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FRIDAY 4:30 PM                                                │
│   ──────────────────────────────────────────────────────────────│
│   😩 "Ugh, I need to do my timesheet before the weekend"        │
│                                                                  │
│   STEP 1: Open Workday (slow, clunky)                           │
│   STEP 2: Try to remember what I did Monday... 🤔               │
│   STEP 3: Open Outlook calendar to jog memory                   │
│   STEP 4: Search for project code... "What was that code?"      │
│   STEP 5: Enter hours for each project                          │
│   STEP 6: Repeat × 5 days                                       │
│   STEP 7: Submit... "Wait, did I bill the client meeting?"      │
│                                                                  │
│   RESULT: 25+ minutes, inaccurate, frustrating                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Future Experience (Delight)

```
┌─────────────────────────────────────────────────────────────────┐
│                 INTELLIGENT TIME ENTRY ASSISTANT                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FRIDAY 4:30 PM (Push Notification)                            │
│   ──────────────────────────────────────────────────────────────│
│   📱 "Your timesheet draft is ready! 38.5 hours across 4        │
│       projects. Tap to review."                                 │
│                                                                  │
│   USER OPENS OPS IQ:                                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  📋 Weekly Time Entry Draft                              │   │
│   │  ─────────────────────────────────────────────────────   │   │
│   │                                                          │   │
│   │  MON 8.0h │ TUE 8.0h │ WED 7.5h │ THU 8.0h │ FRI 7.0h   │   │
│   │                                                          │   │
│   │  ┌────────────────────────────────────────────────────┐ │   │
│   │  │ 📁 Acme Corp - Digital Transformation     18.5h ✏️  │ │   │
│   │  │    Based on: 5 calendar meetings, 3 Workday tasks  │ │   │
│   │  └────────────────────────────────────────────────────┘ │   │
│   │                                                          │   │
│   │  ┌────────────────────────────────────────────────────┐ │   │
│   │  │ 📁 Internal - Training & Development       8.0h ✏️  │ │   │
│   │  │    Based on: 2 training sessions                   │ │   │
│   │  └────────────────────────────────────────────────────┘ │   │
│   │                                                          │   │
│   │  ┌────────────────────────────────────────────────────┐ │   │
│   │  │ 📁 Beta Inc - Audit Support               12.0h ✏️  │ │   │
│   │  │    Based on: 4 meetings, 2 tasks                   │ │   │
│   │  └────────────────────────────────────────────────────┘ │   │
│   │                                                          │   │
│   │  [Save Locally]       [✅ Submit to Workday]             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   RESULT: 2 minutes, accurate, delightful                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### User Scenarios

#### Scenario 1: On-the-Go Entry

```
👤 User finishes client meeting at coffee shop (no VPN)

User: "Log 2 hours for Acme project"
Ops IQ: ✅ Saved locally. Submit when ready.

[Entry stored in Tauri SQLite on user's laptop]
```

#### Scenario 2: Batch Review on Friday

```
📱 Notification: "You have 38.5 hours saved. Ready to submit?"

User opens Ops IQ → Reviews all saved entries → [Submit All]
```

#### Scenario 3: Weekend Catch-up

```
👤 User at home on Saturday, remembers a missed entry

User: "Add 3 hours to Beta project for Wednesday"
Ops IQ: ✅ Saved locally. 41.5 hours total for this week.

Sunday night: User opens app → [Submit to Workday]
```

### Key UX Features

| Feature | User Benefit |
|---------|--------------|
| **Pre-drafted entries** | No manual recall needed |
| **Project auto-complete** | Cached locally, instant search |
| **Smart project matching** | "Client meeting" → Infers project |
| **Conflict detection** | "You have 9 hours on Tuesday - adjust?" |
| **Friday nudge** | Never forget to submit |
| **Voice entry** | "Add 2 hours to Acme audit work" |
| **Edit inline** | Quick adjustments without leaving Ops IQ |
| **Save locally** | Work offline, submit when convenient |
| **Batch submit** | Review all entries before sending |

---

## Architect Perspective

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIME ENTRY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DATA SOURCES                                                   │
│   ──────────────────────────────────────────────────────────────│
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │ M365 Calendar│  │ Workday      │  │ Workday      │          │
│   │ (Graph API)  │  │ Projects     │  │ Time Codes   │          │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│          │                 │                 │                   │
│          └─────────────────┼─────────────────┘                   │
│                            │                                     │
│                            ▼                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 IIS BACKEND                              │   │
│   │  ┌─────────────────────────────────────────────────┐    │   │
│   │  │           TIME ENTRY INFERENCE ENGINE            │    │   │
│   │  │                                                  │    │   │
│   │  │  1. Fetch calendar events (Mon-Fri)             │    │   │
│   │  │  2. Fetch active Workday projects               │    │   │
│   │  │  3. Match events → projects (ML/rules)          │    │   │
│   │  │  4. Calculate hours per project                 │    │   │
│   │  │  5. Generate draft time entries                 │    │   │
│   │  └─────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 LOCAL CACHE (Tauri SQLite)               │   │
│   │  • User's Workday projects (synced daily)               │   │
│   │  • Time codes (synced weekly)                           │   │
│   │  • Saved time entries (offline-ready)                   │   │
│   │  • Historical patterns (for ML)                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 WORKDAY API                              │   │
│   │  POST /timeTracking/submit                              │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   SYNC PHASE (Background, Daily)                                │
│   ──────────────────────────────────────────────────────────────│
│   Workday Projects API → Backend → Local SQLite Cache           │
│   Workday Time Codes API → Backend → Local SQLite Cache         │
│                                                                  │
│   DRAFT GENERATION (Weekly, Thursday Evening)                   │
│   ──────────────────────────────────────────────────────────────│
│   M365 Calendar (Graph) ─┐                                      │
│   Workday Tasks ─────────┼──→ Inference Engine → Draft Entries  │
│   Historical Patterns ───┘                                      │
│                                                                  │
│   USER INTERACTION                                              │
│   ──────────────────────────────────────────────────────────────│
│   Draft → User Review → [Edit] → [Save Locally] or [Submit]    │
│                                                                  │
│   SUBMISSION                                                    │
│   ──────────────────────────────────────────────────────────────│
│   Saved Entries → [Submit] → Workday Time Entry API             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Local Cache Tables

```python
class CachedProject(Base):
    """User's Workday projects cached locally for fast search."""
    __tablename__ = "cached_projects"
    
    id = Column(String, primary_key=True)       # Workday project ID
    user_id = Column(String, index=True)
    name = Column(String)                        # "Acme Corp - Digital Transformation"
    client_name = Column(String)                 # "Acme Corp"
    client_domain = Column(String)               # "acmecorp.com" (for matching)
    project_code = Column(String)                # "ACME-DT-2026"
    time_code = Column(String)                   # "CONSULT-BILLABLE"
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)                 # For smart sorting
    usage_count = Column(Integer, default=0)     # For ML ranking
    synced_at = Column(DateTime)

class CachedTimeCode(Base):
    """Workday time codes cached locally."""
    __tablename__ = "cached_time_codes"
    
    id = Column(String, primary_key=True)
    code = Column(String)
    description = Column(String)
    category = Column(String)                    # "Billable", "Non-Billable", "Admin"
    is_active = Column(Boolean, default=True)
```

### Time Entry Tables

```python
class LocalTimeEntry(Base):
    """Time entry stored locally until submitted to Workday."""
    __tablename__ = "local_time_entries"
    
    id = Column(String, primary_key=True)       # UUID
    user_id = Column(String, index=True)
    
    # Entry details
    week_start = Column(Date)                    # Monday of the week
    project_id = Column(String, ForeignKey("cached_projects.id"))
    project_name = Column(String)                # Cached for offline display
    project_code = Column(String)
    time_code = Column(String)
    
    # Hours per day
    monday_hours = Column(Float, default=0)
    tuesday_hours = Column(Float, default=0)
    wednesday_hours = Column(Float, default=0)
    thursday_hours = Column(Float, default=0)
    friday_hours = Column(Float, default=0)
    
    notes = Column(String)
    
    # Source tracking (for transparency)
    source = Column(String)                      # "draft", "manual", "voice"
    source_events = Column(JSON)                 # Calendar event IDs
    source_tasks = Column(JSON)                  # Workday task IDs
    confidence = Column(Float)                   # ML confidence 0-1
    
    # State machine
    status = Column(String, default="draft")     # draft, saved, pending, submitted, failed
    
    # Timestamps
    created_at = Column(DateTime)
    modified_at = Column(DateTime)
    submitted_at = Column(DateTime, nullable=True)
    
    # Sync info
    workday_entry_id = Column(String, nullable=True)  # After successful submit
    error_message = Column(String, nullable=True)     # If submission failed
```

### Entry States

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIME ENTRY STATES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│   │  DRAFT   │───→│  SAVED   │───→│ PENDING  │───→│SUBMITTED │  │
│   │          │    │ (Local)  │    │ (Queued) │    │(Workday) │  │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│        │                               │                 │       │
│        │                               └────────────────→│       │
│        │                                   (on failure)  │       │
│        │                                                 │       │
│        └─────────────────────────────────────────────────┘       │
│                          (on error, retry)                       │
│                                                                  │
│   DRAFT:     AI-generated, not yet reviewed by user             │
│   SAVED:     User approved, stored locally (offline-ready)      │
│   PENDING:   User clicked submit, waiting for network/API       │
│   SUBMITTED: Successfully sent to Workday                       │
│   FAILED:    Submission error, needs retry                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Inference Engine

### Calendar to Project Matching

```python
class TimeEntryInferenceEngine:
    """Match calendar events to Workday projects for draft generation."""
    
    async def generate_draft(self, user_id: str, week_start: date) -> list[DraftTimeEntry]:
        """Generate draft time entries for a week based on calendar and tasks."""
        
        # 1. Fetch calendar events for the week
        events = await self.graph_client.get_calendar_events(
            user_id=user_id,
            start=week_start,
            end=week_start + timedelta(days=5)
        )
        
        # 2. Fetch user's active Workday projects
        projects = await self.get_cached_projects(user_id)
        
        # 3. Fetch Workday tasks assigned to user
        tasks = await self.workday_client.get_user_tasks(user_id)
        
        # 4. Match events and tasks to projects
        project_hours = defaultdict(lambda: {
            "hours": [0.0] * 5,
            "events": [],
            "tasks": [],
            "confidence": 0.0
        })
        
        for event in events:
            match = self.match_event_to_project(event, projects)
            if match:
                day_index = (event.start.date() - week_start).days
                if 0 <= day_index < 5:
                    duration = (event.end - event.start).total_seconds() / 3600
                    project_hours[match.project.id]["hours"][day_index] += duration
                    project_hours[match.project.id]["events"].append(event.id)
                    project_hours[match.project.id]["confidence"] = max(
                        project_hours[match.project.id]["confidence"],
                        match.confidence
                    )
        
        # 5. Add task-based hours
        for task in tasks:
            if task.project_id and task.estimated_hours:
                day_index = (task.due_date - week_start).days
                if 0 <= day_index < 5:
                    project_hours[task.project_id]["hours"][day_index] += task.estimated_hours
                    project_hours[task.project_id]["tasks"].append(task.id)
        
        # 6. Create draft entries
        drafts = []
        for project_id, data in project_hours.items():
            project = next(p for p in projects if p.id == project_id)
            draft = LocalTimeEntry(
                id=str(uuid.uuid4()),
                user_id=user_id,
                week_start=week_start,
                project_id=project_id,
                project_name=project.name,
                project_code=project.project_code,
                time_code=project.time_code,
                monday_hours=data["hours"][0],
                tuesday_hours=data["hours"][1],
                wednesday_hours=data["hours"][2],
                thursday_hours=data["hours"][3],
                friday_hours=data["hours"][4],
                source="draft",
                source_events=data["events"],
                source_tasks=data["tasks"],
                confidence=data["confidence"],
                status="draft",
                created_at=datetime.utcnow()
            )
            drafts.append(draft)
        
        return drafts
    
    def match_event_to_project(self, event: CalendarEvent, projects: list[Project]) -> MatchResult:
        """Smart matching using multiple signals."""
        
        # Signal 1: Explicit project mention in title/body
        for project in projects:
            if project.client_name.lower() in event.subject.lower():
                return MatchResult(project=project, confidence=0.95, reason="title_match")
            if project.project_code in (event.body or ""):
                return MatchResult(project=project, confidence=0.99, reason="code_match")
        
        # Signal 2: Attendee domain matching (client contacts)
        event_domains = {
            a.email.split("@")[1] 
            for a in event.attendees 
            if a.email and "@" in a.email
        }
        for project in projects:
            if project.client_domain and project.client_domain in event_domains:
                return MatchResult(project=project, confidence=0.85, reason="attendee_match")
        
        # Signal 3: Historical patterns (ML model)
        if self.ml_model:
            prediction = self.ml_model.predict(
                event_title=event.subject,
                event_duration_minutes=int((event.end - event.start).total_seconds() / 60),
                attendee_count=len(event.attendees),
                day_of_week=event.start.weekday(),
                user_projects=[p.id for p in projects]
            )
            if prediction.confidence > 0.8:
                project = next((p for p in projects if p.id == prediction.project_id), None)
                if project:
                    return MatchResult(project=project, confidence=prediction.confidence, reason="ml_match")
        
        # Signal 4: Default to most-used project for ambiguous internal meetings
        if not event.attendees or all("@armanino" in a.email for a in event.attendees):
            most_used = max(projects, key=lambda p: p.usage_count, default=None)
            if most_used:
                return MatchResult(project=most_used, confidence=0.5, reason="most_used_default")
        
        return None
```

---

## Frontend Implementation

### Local Storage Service

```typescript
// src/services/TimeEntryLocalStorage.ts
import Database from '@tauri-apps/plugin-sql';

class TimeEntryLocalStorage {
  private db: Database;
  
  async init() {
    this.db = await Database.load('sqlite:time_entries.db');
    
    // Create tables
    await this.db.execute(`
      CREATE TABLE IF NOT EXISTS cached_projects (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT,
        client_name TEXT,
        project_code TEXT,
        time_code TEXT,
        is_active INTEGER DEFAULT 1,
        usage_count INTEGER DEFAULT 0,
        last_used DATETIME,
        synced_at DATETIME
      )
    `);
    
    await this.db.execute(`
      CREATE TABLE IF NOT EXISTS local_time_entries (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        week_start DATE,
        project_id TEXT,
        project_name TEXT,
        project_code TEXT,
        time_code TEXT,
        monday_hours REAL DEFAULT 0,
        tuesday_hours REAL DEFAULT 0,
        wednesday_hours REAL DEFAULT 0,
        thursday_hours REAL DEFAULT 0,
        friday_hours REAL DEFAULT 0,
        notes TEXT,
        source TEXT,
        source_events TEXT,
        confidence REAL,
        status TEXT DEFAULT 'saved',
        created_at DATETIME,
        modified_at DATETIME,
        submitted_at DATETIME,
        workday_entry_id TEXT,
        error_message TEXT
      )
    `);
    
    // Create indexes
    await this.db.execute(
      'CREATE INDEX IF NOT EXISTS idx_entries_user_week ON local_time_entries(user_id, week_start)'
    );
    await this.db.execute(
      'CREATE INDEX IF NOT EXISTS idx_entries_status ON local_time_entries(status)'
    );
  }
  
  // Project cache methods
  async syncProjects(userId: string): Promise<void> {
    const projects = await fetch(`/api/v1/user/${userId}/workday-projects`);
    const data = await projects.json();
    
    for (const project of data.projects) {
      await this.db.execute(`
        INSERT OR REPLACE INTO cached_projects 
        (id, user_id, name, client_name, project_code, time_code, is_active, synced_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        project.id, userId, project.name, project.clientName, 
        project.projectCode, project.timeCode, project.isActive ? 1 : 0,
        new Date().toISOString()
      ]);
    }
  }
  
  async searchProjects(userId: string, query: string): Promise<Project[]> {
    return this.db.select(`
      SELECT * FROM cached_projects 
      WHERE user_id = ? AND is_active = 1
        AND (name LIKE ? OR project_code LIKE ? OR client_name LIKE ?)
      ORDER BY usage_count DESC, last_used DESC
      LIMIT 10
    `, [userId, `%${query}%`, `%${query}%`, `%${query}%`]);
  }
  
  // Time entry methods
  async saveEntry(entry: TimeEntry): Promise<void> {
    await this.db.execute(`
      INSERT OR REPLACE INTO local_time_entries 
      (id, user_id, week_start, project_id, project_name, project_code, time_code,
       monday_hours, tuesday_hours, wednesday_hours, thursday_hours, friday_hours,
       notes, source, source_events, confidence, status, created_at, modified_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      entry.id || crypto.randomUUID(),
      entry.userId,
      entry.weekStart,
      entry.projectId,
      entry.projectName,
      entry.projectCode,
      entry.timeCode,
      entry.mondayHours,
      entry.tuesdayHours,
      entry.wednesdayHours,
      entry.thursdayHours,
      entry.fridayHours,
      entry.notes,
      entry.source || 'manual',
      JSON.stringify(entry.sourceEvents || []),
      entry.confidence || 1.0,
      'saved',
      entry.createdAt || new Date().toISOString(),
      new Date().toISOString()
    ]);
    
    // Update project usage
    await this.db.execute(`
      UPDATE cached_projects 
      SET usage_count = usage_count + 1, last_used = ?
      WHERE id = ?
    `, [new Date().toISOString(), entry.projectId]);
  }
  
  async getEntriesByWeek(userId: string, weekStart: Date): Promise<TimeEntry[]> {
    return this.db.select(
      'SELECT * FROM local_time_entries WHERE user_id = ? AND week_start = ? ORDER BY project_name',
      [userId, weekStart.toISOString().split('T')[0]]
    );
  }
  
  async getSavedEntries(userId: string): Promise<TimeEntry[]> {
    return this.db.select(
      'SELECT * FROM local_time_entries WHERE user_id = ? AND status = "saved" ORDER BY week_start DESC',
      [userId]
    );
  }
  
  async getPendingEntries(userId: string): Promise<TimeEntry[]> {
    return this.db.select(
      'SELECT * FROM local_time_entries WHERE user_id = ? AND status IN ("saved", "pending") ORDER BY week_start',
      [userId]
    );
  }
  
  async getTotalSavedHours(userId: string): Promise<{ hours: number; weeks: number }> {
    const result = await this.db.select(`
      SELECT 
        SUM(monday_hours + tuesday_hours + wednesday_hours + thursday_hours + friday_hours) as total_hours,
        COUNT(DISTINCT week_start) as week_count
      FROM local_time_entries 
      WHERE user_id = ? AND status = 'saved'
    `, [userId]);
    
    return {
      hours: result[0]?.total_hours || 0,
      weeks: result[0]?.week_count || 0
    };
  }
  
  async updateStatus(entryIds: string[], status: string, errorMessage?: string): Promise<void> {
    for (const id of entryIds) {
      await this.db.execute(
        'UPDATE local_time_entries SET status = ?, error_message = ?, modified_at = ? WHERE id = ?',
        [status, errorMessage || null, new Date().toISOString(), id]
      );
    }
  }
  
  async markAsSubmitted(entryIds: string[], workdayIds: Record<string, string>): Promise<void> {
    for (const id of entryIds) {
      await this.db.execute(
        'UPDATE local_time_entries SET status = "submitted", submitted_at = ?, workday_entry_id = ? WHERE id = ?',
        [new Date().toISOString(), workdayIds[id] || null, id]
      );
    }
  }
  
  async deleteEntry(entryId: string): Promise<void> {
    await this.db.execute('DELETE FROM local_time_entries WHERE id = ?', [entryId]);
  }
}

export const timeEntryStorage = new TimeEntryLocalStorage();
```

### Sync Service

```typescript
// src/services/TimeEntrySyncService.ts
class TimeEntrySyncService {
  
  async submitToWorkday(entryIds: string[]): Promise<SubmitResult> {
    const entries = await timeEntryStorage.getEntriesByIds(entryIds);
    
    // Mark as pending
    await timeEntryStorage.updateStatus(entryIds, 'pending');
    
    try {
      // Submit to backend (which calls Workday API)
      const response = await fetch('/api/v1/workday/time-entries/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entries })
      });
      
      if (response.ok) {
        const result = await response.json();
        await timeEntryStorage.markAsSubmitted(entryIds, result.workdayIds);
        
        return { 
          success: true, 
          submitted: entries.length,
          workdayIds: result.workdayIds 
        };
      } else {
        const error = await response.text();
        throw new Error(error);
      }
    } catch (error) {
      // Mark as saved (retry-able), not failed
      await timeEntryStorage.updateStatus(entryIds, 'saved', error.message);
      return { success: false, error: error.message };
    }
  }
  
  async submitAllSaved(userId: string): Promise<SubmitResult> {
    const entries = await timeEntryStorage.getSavedEntries(userId);
    if (entries.length === 0) {
      return { success: true, submitted: 0 };
    }
    return this.submitToWorkday(entries.map(e => e.id));
  }
  
  async fetchAndStoreDrafts(userId: string, weekStart: Date): Promise<void> {
    const response = await fetch(
      `/api/v1/time-entries/draft?week_start=${weekStart.toISOString().split('T')[0]}`
    );
    const drafts = await response.json();
    
    for (const draft of drafts.entries) {
      await timeEntryStorage.saveEntry({
        ...draft,
        status: 'draft'
      });
    }
  }
}

export const timeEntrySyncService = new TimeEntrySyncService();
```

---

## MCP Tools

```python
MCP_TIME_ENTRY_TOOLS = {
    "get_draft_timesheet": {
        "description": "Get the AI-generated draft timesheet for the current or specified week",
        "parameters": {
            "week_offset": "int, optional (0=current, -1=last week)"
        },
        "returns": "Draft time entries with project allocations"
    },
    "get_saved_entries": {
        "description": "Get all locally saved time entries not yet submitted",
        "parameters": {},
        "returns": "List of saved entries grouped by week"
    },
    "add_time_entry": {
        "description": "Add or update a time entry for a specific project and day",
        "parameters": {
            "project_query": "str (name or code to search)",
            "day": "str (monday, tuesday, etc. or date)",
            "hours": "float",
            "notes": "str, optional"
        },
        "returns": "Confirmation of saved entry"
    },
    "search_projects": {
        "description": "Search user's available Workday projects",
        "parameters": {
            "query": "str"
        },
        "returns": "Matching projects with codes and time codes"
    },
    "submit_timesheet": {
        "description": "Submit saved time entries to Workday",
        "parameters": {
            "week_start": "date, optional (default: all saved)"
        },
        "returns": "Submission confirmation with Workday IDs"
    },
    "delete_entry": {
        "description": "Delete a saved time entry",
        "parameters": {
            "entry_id": "str"
        },
        "returns": "Confirmation"
    }
}
```

---

## Conversational Interface Examples

### Example 1: Quick Entry

```
USER: "Log 2 hours on Acme for today's client call"

OPS IQ: ✅ Saved locally:
        📁 Acme Corp - Digital Transformation (ACME-DT-2026)
        📅 Tuesday, Jan 14: +2 hours (6 total for today)
        
        This week so far: 22.5 hours
        
        [View Week] [Submit Now]
```

### Example 2: Voice Entry

```
USER: "I spent 3 hours on the Beta audit yesterday and 2 hours on training today"

OPS IQ: ✅ Saved 2 entries:
        
        📁 Beta Inc - Audit (BETA-AUD-2026)
        📅 Monday, Jan 13: 3 hours
        
        📁 Internal - Training (INT-TRAIN)
        📅 Tuesday, Jan 14: 2 hours
        
        This week so far: 27.5 hours
```

### Example 3: Review and Submit

```
USER: "Show me my time for this week"

OPS IQ: 📋 Week of Jan 13-17, 2026
        
        ┌────────────────────────────────────────┐
        │ Project                    │ Hours    │
        ├────────────────────────────────────────┤
        │ Acme Corp - Digital Trans. │ 18.5     │
        │ Beta Inc - Audit           │ 12.0     │
        │ Internal - Training        │  8.0     │
        ├────────────────────────────────────────┤
        │ TOTAL                      │ 38.5     │
        └────────────────────────────────────────┘
        
        Status: 🟡 Saved locally (not submitted)
        
        [Edit] [Submit to Workday]

USER: "Submit it"

OPS IQ: ✅ Submitted 38.5 hours to Workday!
        Confirmation: WD-2026-0117-001
```

---

## Push Notifications

### Friday Nudge

```python
# Scheduled job: Friday 2:00 PM
async def send_friday_nudge():
    users = await get_users_with_unsaved_drafts()
    
    for user in users:
        saved_stats = await get_user_saved_stats(user.id)
        
        if saved_stats.hours > 0:
            await send_push_notification(
                user_id=user.id,
                title="📋 Time to submit your timesheet!",
                body=f"You have {saved_stats.hours} hours saved. Review and submit before the weekend.",
                data={"action": "open_timesheet"}
            )
        else:
            # Generate draft and nudge
            draft = await generate_weekly_draft(user.id)
            await send_push_notification(
                user_id=user.id,
                title="📋 Your timesheet draft is ready!",
                body=f"{draft.total_hours} hours across {len(draft.projects)} projects. Tap to review.",
                data={"action": "open_draft"}
            )
```

### Overdue Reminder

```python
# Scheduled job: Monday 9:00 AM
async def send_overdue_reminder():
    users = await get_users_with_unsubmitted_past_weeks()
    
    for user, weeks in users:
        await send_push_notification(
            user_id=user.id,
            title="⚠️ Overdue timesheets",
            body=f"You have {len(weeks)} weeks not yet submitted to Workday.",
            data={"action": "open_saved_entries"}
        )
```

---

## Implementation Phases

| Phase | Scope | Timeline | Deliverables |
|-------|-------|----------|--------------|
| **Phase 1** | Local cache + manual entry | 2 weeks | Project cache, basic entry UI, save locally |
| **Phase 2** | Calendar matching (rules) | 3 weeks | Graph API integration, rule-based matching |
| **Phase 3** | Draft generation + review | 2 weeks | Draft UI, edit flow, submit to Workday |
| **Phase 4** | Push notifications + nudge | 1 week | Friday reminder, overdue alerts |
| **Phase 5** | ML matching + voice | 4 weeks | Confidence scoring, pattern learning, voice input |

---

## Summary

### Product Fit

| Dimension | Assessment |
|-----------|------------|
| **Problem-Solution Fit** | ✅ Universal pain point in professional services |
| **Value Proposition** | ✅ 80% time savings, 15% revenue recovery |
| **Differentiation** | ✅ AI-assisted, offline-first, conversational |
| **Technical Feasibility** | ✅ All APIs available, fits Tauri architecture |

### Key Benefits

| Stakeholder | Benefit |
|-------------|---------|
| **Individual User** | Less friction, faster entry, offline capability |
| **Management** | Better compliance, accurate billing |
| **Finance** | Captured revenue, fewer corrections |
| **IT** | Reduced Workday support tickets |

---

## v2 Refinements (January 2026)

> These refinements were captured during brainstorming sessions to address real-world usage patterns.

### Time Coding Models

| Time Type | Requires Project? | Requires Task? | Example |
|-----------|-------------------|----------------|---------|
| **By Role** | ✅ Yes | ❌ No | "2h consulting for Acme" |
| **By Project Task** | ✅ Yes | ✅ Yes | "3h on Task #1234" |
| **Internal/Admin** | ❌ No | ❌ No | "1h Firm Meeting" |

### No-Project Time Codes

```yaml
internal_time_codes:
  - code: "FIRM-MTG"
    label: "Firm Meetings"
    requires_project: false
  - code: "PROF-DEV"
    label: "Professional Development"
    requires_project: false
  - code: "ADMIN"
    label: "Administrative"
    requires_project: false
  - code: "PTO"
    label: "Paid Time Off"
    requires_project: false
    auto_detect: true
```

### Time Off Detection

Auto-detect from:
- **M365 Calendar**: "Out of Office" status
- **Workday**: PTO/Leave records
- **Calendar events**: "Vacation", "OOO", "Personal Day"

When detected → Pre-fill 8h PTO for that day.

---

### Nudge Strategy

| Day | Time | Condition | Message |
|-----|------|-----------|---------|
| Mon-Thu | 5:00 PM | Hours < 8 today | "📊 Log your hours before leaving" |
| Thu | 4:00 PM | Total < 32h | "⚠️ Timesheet due Friday - hours missing" |
| Fri | All day | Not submitted | "🚨 Submit your timesheet before EOD!" |

**MVP Approach**: In-app banners on login (no push infrastructure)
**V2 Approach**: Web Push API or ntfy.sh for background notifications

---

### Voice Entry

| Option | Technology | Complexity |
|--------|------------|------------|
| **MVP** | Web Speech API (browser) | Low |
| **V2** | Azure Speech-to-Text | Medium |
| **V3** | Gemini Multimodal (audio) | High |

Example flow:
```
User (voice): "Record 2 hours for the Acme client meeting"
Agent: ✅ Added 2 hours to Acme Corp - Consulting
       📅 Today (Wed): 2.0h
       [✏️ Edit] [💾 Save Draft]
```

---

### Hybrid Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID STORAGE FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   USER: "Log 2 hours for Acme project"                          │
│                                                                  │
│   1. Write to IndexedDB immediately (< 10ms, offline-ready)     │
│   2. Queue entry for backend sync                                │
│   3. Background sync to PostgreSQL (batched every 5 seconds)    │
│   4. Mark as "synced" in IndexedDB on success                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Storage Backend Toggle**:
```typescript
const config = {
  primary: 'indexeddb' | 'postgres',
  syncEnabled: true,
  syncInterval: 5000,  // ms
  batchSize: 50
};
```

---

### Multi-Device Sync

**PostgreSQL is the source of truth.**

| Action | Flow |
|--------|------|
| User logs time on laptop | IndexedDB → Push to PostgreSQL |
| User opens phone | Pull from PostgreSQL → Update IndexedDB |
| Conflict (both edited) | Server timestamp wins + notify user |

**Sync Triggers**:
- App opens (full sync)
- User adds entry (push)
- Every 60 seconds (background check)
- Network reconnects (full sync)

---

### Data Retention & Purging

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Submitted entries | 90 days | Historical reference |
| Draft entries | Forever | User might still need them |
| Pending sync | Forever | Must not lose data |
| Cached projects | 30 days | Re-sync from server |

**Auto-Cleanup** runs on app startup:
```typescript
// Delete submitted entries older than 90 days
await db.delete('entries', 
  IDBKeyRange.upperBound(cutoffDate)
);
```

**Storage Monitoring**: If usage > 80% quota, trigger aggressive cleanup (30 days).

---

### Cross-Platform Support

| Platform | Storage | Sync |
|----------|---------|------|
| Web Browser | IndexedDB | ✅ PostgreSQL |
| PWA (installed) | IndexedDB | ✅ PostgreSQL |
| Tauri Desktop | SQLite preferred | ✅ PostgreSQL |
| Tauri Mobile | SQLite preferred | ✅ PostgreSQL |

---

### Updated Phase Plan

| Phase | Scope | Effort | Deliverable |
|-------|-------|--------|-------------|
| **Phase 1** | Chat-based time entry + PostgreSQL storage | 1 week | "Log 2h for Acme" works |
| **Phase 2** | Weekly grid UI + editable drafts | 1 week | Matches Workday layout |
| **Phase 3** | Calendar integration + auto-draft | 2 weeks | AI pre-fills from M365 |
| **Phase 4** | In-app nudge banners | 3 days | Login reminders |
| **Phase 5** | Multi-device sync + IndexedDB | 1 week | Offline-first |
| **Phase 6** | Voice entry (Web Speech API) | 3 days | Voice logging |
| **Phase 7** | Web Push notifications | 1 week | Background nudges |

