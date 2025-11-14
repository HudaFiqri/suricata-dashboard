# UI/UX Design & Mockups

## Overview

New user interface pages for remote agent management and monitoring.

**Design Principles:**
- Clean, modern interface
- Real-time updates (WebSocket)
- Responsive (mobile-friendly)
- Consistent with existing dashboard theme
- Dark mode support

---

## Page Structure

```
Suricata Dashboard
├── Dashboard (/)                    # Overview of all agents
├── Agents (/agents)
│   ├── List (/agents)              # All agents
│   ├── Detail (/agents/{id})       # Single agent detail
│   ├── Register (/agents/register) # Add new agent
│   └── Install (/agents/install)   # Installation guide
│
├── Monitoring (/monitor)
│   ├── Real-time (/monitor/realtime)  # Live event stream
│   ├── Alerts (/monitor/alerts)       # Alert feed
│   └── Logs (/monitor/logs)           # Log stream
│
├── Config (/config)
│   ├── Editor (/config/{agent_id})     # Edit config
│   ├── History (/config/{agent_id}/history)  # Version history
│   └── Diff (/config/{agent_id}/diff)  # Compare versions
│
├── Query (/query)
│   ├── Events (/query/events)      # Search events
│   ├── Logs (/query/logs)          # Search logs
│   └── Analytics (/query/analytics)  # Charts & graphs
│
└── PCAP (/pcap)
    └── Captures (/pcap)            # PCAP management
```

---

## 1. Dashboard (Home Page)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Suricata Dashboard                         [User] [Settings]  │
├────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │  Agents    │  │   Events   │  │   Alerts   │  │   CPU    │ │
│  │            │  │            │  │            │  │          │ │
│  │    10      │  │  1.2M/hr   │  │    245     │  │   42%    │ │
│  │   Online   │  │            │  │   Last 24h │  │   Avg    │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Agent Status                                           │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Name               Status    CPU   Mem   Last Seen     │  │
│  │  ─────────────────  ────────  ────  ────  ─────────────  │ │
│  │  🟢 web-server-01    Online    45%   1GB   2 min ago    │  │
│  │  🟢 db-server-01     Online    32%   2GB   1 min ago    │  │
│  │  🔴 app-server-01    Offline   -     -     10 min ago   │  │
│  │  🟢 dmz-fw-01        Online    65%   512M  30 sec ago   │  │
│  │                                                         │  │
│  │  [View All Agents]                                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────┐  ┌──────────────────────────┐ │
│  │  Recent Alerts             │  │  Top Signatures          │ │
│  ├────────────────────────────┤  ├──────────────────────────┤ │
│  │  [!] ET MALWARE Botnet     │  │  SQL Injection (125)     │ │
│  │      web-server-01         │  │  Port Scan (98)          │ │
│  │      2 min ago             │  │  Malware Download (67)   │ │
│  │                            │  │  Brute Force (45)        │ │
│  │  [!] SQL Injection         │  │  XSS Attempt (32)        │ │
│  │      db-server-01          │  │                          │ │
│  │      5 min ago             │  │  [View All]              │ │
│  │                            │  │                          │ │
│  │  [View All Alerts]         │  │                          │ │
│  └────────────────────────────┘  └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Real-time agent status (WebSocket updates)
- Quick stats cards
- Recent alerts feed
- Agent health indicators
- Click to drill-down

---

## 2. Agent List Page (/agents)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Agents                                [+ Register New Agent]  │
├────────────────────────────────────────────────────────────────┤
│  🔍 Search: [_____________]  Status: [All ▾]  Tags: [All ▾]   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Agent Cards                                             │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  ┌────────────────────────────┐  ┌────────────────────┐ │ │
│  │  │ 🟢 web-server-01            │  │ 🟢 db-server-01     │ │ │
│  │  │ ──────────────────────────  │  │ ──────────────────  │ │ │
│  │  │ Status: Online              │  │ Status: Online      │ │ │
│  │  │ IP: 192.168.1.100           │  │ IP: 192.168.1.101   │ │ │
│  │  │ Suricata: 7.0.2             │  │ Suricata: 7.0.2     │ │ │
│  │  │ Tags: production, web       │  │ Tags: production,db │ │ │
│  │  │                             │  │                     │ │ │
│  │  │ CPU: ████████░░ 45%         │  │ CPU: ████░░░░░░ 32% │ │ │
│  │  │ Mem: ████░░░░░░ 1024MB      │  │ Mem: ████████░░ 2GB │ │ │
│  │  │ Alerts: 12 (1h)             │  │ Alerts: 5 (1h)      │ │ │
│  │  │                             │  │                     │ │ │
│  │  │ [View] [Config] [Commands]  │  │ [View] [Config]     │ │ │
│  │  └────────────────────────────┘  └────────────────────┘ │ │
│  │                                                          │ │
│  │  ┌────────────────────────────┐  ┌────────────────────┐ │ │
│  │  │ 🔴 app-server-01 (OFFLINE)  │  │ 🟢 dmz-fw-01        │ │ │
│  │  │ ──────────────────────────  │  │ ──────────────────  │ │ │
│  │  │ Last seen: 10 min ago       │  │ Status: Online      │ │ │
│  │  │ IP: 192.168.1.102           │  │ IP: 10.0.0.1        │ │ │
│  │  │                             │  │ ...                 │ │ │
│  │  │ [View] [Troubleshoot]       │  │ [View] [Config]     │ │ │
│  │  └────────────────────────────┘  └────────────────────┘ │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Showing 4 of 10 agents                          [1][2][3]    │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Card-based layout
- Real-time status indicators (🟢 online, 🔴 offline, 🟡 warning)
- Search and filter
- Quick actions (View, Config, Commands)
- Health metrics visualization

---

## 3. Agent Detail Page (/agents/{id})

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  ← Agents / web-server-01                          [⚙ Config] │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Agent Information                                      │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Name: web-server-01            Status: 🟢 Online        │  │
│  │  Hostname: web-prod-01          Suricata: v7.0.2        │  │
│  │  IP: 192.168.1.100              Agent: v1.0.0           │  │
│  │  Tags: [production] [web] [critical]                    │  │
│  │  Last Seen: 30 seconds ago      Uptime: 2 days 5h 32m   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Health Metrics                                         │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  CPU Usage (1h)                                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │    %                                              │   │  │
│  │  │ 100│                                              │   │  │
│  │  │  75│        ╱╲                                    │   │  │
│  │  │  50│   ╱╲  ╱  ╲  ╱╲                              │   │  │
│  │  │  25│  ╱  ╲╱    ╲╱  ╲                             │   │  │
│  │  │   0└──────────────────────────────────────────── │   │  │
│  │  │       -60m    -30m       now                      │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                         │  │
│  │  Memory: 1024MB / 16GB (6%)     Disk: 65GB / 100GB    │  │
│  │  Network: ↓ 125Mbps ↑ 45Mbps                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Suricata Statistics (Last Hour)                        │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Packets Processed: 1,245,678    Dropped: 125 (0.01%)  │  │
│  │  Flows: 45,231                   Alerts: 12             │  │
│  │  TCP: 85%   UDP: 12%   Other: 3%                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Recent Events                              [View All]  │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  2 min ago  [ALERT]  ET MALWARE Botnet Traffic         │  │
│  │  5 min ago  [FLOW]   TCP 192.168.1.50 → 8.8.8.8:443    │  │
│  │  8 min ago  [ALERT]  SQL Injection Attempt             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Actions                                                │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  [Edit Config]  [Reload Suricata]  [Restart Suricata]  │  │
│  │  [Update Rules] [Capture PCAP]     [View Logs]         │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Comprehensive agent info
- Real-time health metrics with charts
- Suricata statistics
- Recent events feed
- Quick action buttons
- WebSocket live updates

---

## 4. Register New Agent (/agents/register)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Register New Agent                           ← Back to Agents │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Step 1: Agent Information                              │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Agent Name: [__________________________________]         │  │
│  │  (Optional, leave blank to use hostname)                │  │
│  │                                                         │  │
│  │  Tags: [production] [web] [critical] [+Add]            │  │
│  │                                                         │  │
│  │  [Next: Generate Install Command]                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Step 2: Installation                                   │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Run this command on your Suricata host:                │  │
│  │                                                         │  │
│  │  ┌───────────────────────────────────────────────────┐ │  │
│  │  │ curl -sSL https://dashboard.example.com/agent/    │ │  │
│  │  │ install.sh?token=abc123 | sudo bash               │ │  │
│  │  │                                         [📋 Copy]  │ │  │
│  │  └───────────────────────────────────────────────────┘ │  │
│  │                                                         │  │
│  │  Or download and review first:                         │  │
│  │  [📥 Download Installer Script]                         │  │
│  │                                                         │  │
│  │  ℹ️ This token is valid for 24 hours                   │  │
│  │                                                         │  │
│  │  ┌───────────────────────────────────────────────────┐ │  │
│  │  │ 🔄 Waiting for agent to connect...                │ │  │
│  │  │                                                   │ │  │
│  │  │    [   ] Agent installed                          │ │  │
│  │  │    [   ] Connection established                   │ │  │
│  │  │    [   ] Authentication successful                │ │  │
│  │  │                                                   │ │  │
│  │  │    This will update automatically when agent      │ │  │
│  │  │    connects.                                      │ │  │
│  │  └───────────────────────────────────────────────────┘ │  │
│  │                                                         │  │
│  │  [Cancel]                                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Step 3: Verification                                   │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  ✅ Agent connected successfully!                        │  │
│  │                                                         │  │
│  │  Agent: web-server-01                                   │  │
│  │  IP: 192.168.1.100                                      │  │
│  │  Suricata Version: 7.0.2                                │  │
│  │                                                         │  │
│  │  [Go to Agent Dashboard]  [Register Another Agent]     │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Step-by-step wizard
- One-liner install command with copy button
- Real-time connection status (WebSocket)
- Auto-advance when agent connects
- Download option for security review

---

## 5. Config Editor (/config/{agent_id})

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Config Editor: web-server-01                  [History] [↻]   │
├────────────────────────────────────────────────────────────────┤
│  File: [suricata.yaml ▾]        Version: 5 (Active)            │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  YAML Editor (Syntax Highlighting)                      │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │ 1  # Suricata Configuration                             │  │
│  │ 2                                                        │  │
│  │ 3  vars:                                                 │  │
│  │ 4    address-groups:                                     │  │
│  │ 5      HOME_NET: "[192.168.0.0/16,10.0.0.0/8]"         │  │
│  │ 6      EXTERNAL_NET: "!$HOME_NET"                       │  │
│  │ 7                                                        │  │
│  │ 8  outputs:                                              │  │
│  │ 9    - eve-log:                                          │  │
│  │10        enabled: yes                                    │  │
│  │11        filetype: regular                               │  │
│  │12        filename: eve.json                              │  │
│  │13        types:                                          │  │
│  │14          - alert:                                      │  │
│  │15              payload: yes                              │  │
│  │16              metadata: yes                             │  │
│  │17          - http:                                       │  │
│  │18              extended: yes                             │  │
│  │...                                                        │  │
│  │                                                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Validation:                                            │  │
│  │  ✅ YAML syntax valid                                     │  │
│  │  ⚠️  Warning: Line 42 uses deprecated option 'old-opt'   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  Change Notes: [_____________________________________________] │
│                                                                │
│  [Validate Only] [Save Draft] [Apply to Agent]                │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  ℹ️ Apply to Agent will:                                  │  │
│  │  1. Validate configuration                              │  │
│  │  2. Push to agent                                       │  │
│  │  3. Test configuration                                  │  │
│  │  4. Gracefully reload Suricata                          │  │
│  │                                                         │  │
│  │  Estimated downtime: < 1 second                         │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Full YAML editor with syntax highlighting (Ace Editor)
- Real-time validation
- Version control
- Change notes
- Preview mode
- Apply with confirmation

---

## 6. Live Monitoring (/monitor/realtime)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Live Monitor                           [⏸ Pause] [📥 Export]  │
├────────────────────────────────────────────────────────────────┤
│  Filters: Agent: [All ▾]  Type: [All ▾]  Severity: [All ▾]     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Event Stream (Real-time via WebSocket)                 │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  🔴 10:32:15  web-server-01  [ALERT] Severity: 1         │  │
│  │     ET MALWARE Botnet Traffic Detected                   │  │
│  │     192.168.1.50:54321 → 8.8.8.8:443                     │  │
│  │     [View Details] [PCAP]                                │  │
│  │                                                          │  │
│  │  ─────────────────────────────────────────────────────   │  │
│  │                                                          │  │
│  │  🟡 10:32:10  db-server-01  [ALERT] Severity: 2          │  │
│  │     SQL Injection Attempt                                │  │
│  │     10.0.1.100:48923 → 10.0.1.101:3306                   │  │
│  │     [View Details] [Block IP]                            │  │
│  │                                                          │  │
│  │  ─────────────────────────────────────────────────────   │  │
│  │                                                          │  │
│  │  ⚪ 10:32:08  dmz-fw-01  [HTTP]                          │  │
│  │     GET /api/users HTTP/1.1                              │  │
│  │     Client: 203.0.113.45                                 │  │
│  │     [View Details]                                       │  │
│  │                                                          │  │
│  │  ─────────────────────────────────────────────────────   │  │
│  │                                                          │  │
│  │  🟢 10:32:05  web-server-01  [FLOW]                      │  │
│  │     TCP Flow Completed                                   │  │
│  │     Duration: 2.5s, Bytes: 15KB                          │  │
│  │                                                          │  │
│  │  ─────────────────────────────────────────────────────   │  │
│  │                                                          │  │
│  │  [Load More] (Auto-scroll: ON)                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  📊 Rate: 125 events/sec   Total (session): 3,456             │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Real-time event feed (WebSocket streaming)
- Color-coded by severity/type
- Auto-scroll option
- Pause/resume
- Filter by agent, type, severity
- Quick actions per event
- Export to JSON/CSV

---

## 7. Query Interface (/query/events)

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Query Events                                                  │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Query Builder                                          │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Time Range: [Last 24 hours ▾]                          │  │
│  │  Custom: [2025-01-14 00:00] to [2025-01-14 23:59]       │  │
│  │                                                         │  │
│  │  Filters:                                               │  │
│  │  ┌────────────────────────────────────────────────┐    │  │
│  │  │ Agent:      [web-server-01  ▾]                  │    │  │
│  │  │ Event Type: [alert          ▾]                  │    │  │
│  │  │ Severity:   [1,2            ▾]                  │    │  │
│  │  │ Source IP:  [192.168.1.*    ]                   │    │  │
│  │  │ Dest IP:    [              ]                    │    │  │
│  │  │ Signature:  [SQL Injection  ]                   │    │  │
│  │  │             [+ Add Filter]                       │    │  │
│  │  └────────────────────────────────────────────────┘    │  │
│  │                                                         │  │
│  │  [Reset] [Search]                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Results (245 events)                    [Export CSV]   │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Timestamp          Agent          Signature      Sev   │  │
│  │  ────────────────   ──────────────  ────────────  ───   │  │
│  │  2025-01-14 10:32   web-server-01   SQL Inject.   1    │  │
│  │  2025-01-14 10:30   web-server-01   XSS Attempt   2    │  │
│  │  2025-01-14 10:28   db-server-01    Brute Force   1    │  │
│  │  ...                                                    │  │
│  │                                                         │  │
│  │  [1][2][3]...[25]                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Visualization                              [Chart Type]│  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  Events Over Time                                       │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 50│      █                                        │   │  │
│  │  │ 40│     ███                                       │   │  │
│  │  │ 30│    █████                                      │   │  │
│  │  │ 20│  ████████                                     │   │  │
│  │  │ 10│██████████                                     │   │  │
│  │  │  0└────────────────────────────────────────────── │   │  │
│  │  │     00:00  06:00  12:00  18:00  24:00            │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Features
- Query builder with multiple filters
- Time range selection
- Results table with pagination
- Export to CSV/JSON
- Visualizations (charts)
- Saved queries

---

## Color Scheme & Theme

### Light Mode
```css
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --text-primary: #333333;
    --text-secondary: #666666;
    --border: #dddddd;
    --accent: #0066cc;
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
}
```

### Dark Mode
```css
:root[data-theme="dark"] {
    --bg-primary: #1e1e1e;
    --bg-secondary: #2d2d2d;
    --text-primary: #e0e0e0;
    --text-secondary: #a0a0a0;
    --border: #444444;
    --accent: #4a9eff;
    --success: #3fb950;
    --warning: #f0ad4e;
    --danger: #f85149;
}
```

---

## Responsive Design

### Breakpoints
- Desktop: >= 1200px
- Tablet: 768px - 1199px
- Mobile: < 768px

### Mobile Adaptations
- Collapsible sidebar
- Stacked cards instead of grid
- Simplified tables
- Touch-friendly buttons
- Bottom navigation bar

---

## JavaScript Libraries

- **Chart.js**: Data visualization
- **Ace Editor**: Code/YAML editor
- **Socket.IO**: WebSocket client
- **Moment.js**: Time formatting
- **DataTables**: Advanced tables (optional)
- **Tailwind CSS** or **Bootstrap 5**: UI framework

---

## Next Steps
- [ ] Create HTML templates
- [ ] Implement CSS styling
- [ ] Write JavaScript for real-time updates
- [ ] Connect WebSocket to UI
- [ ] Add interactivity (buttons, forms)
- [ ] Test responsive design
- [ ] Accessibility (ARIA labels, keyboard nav)
