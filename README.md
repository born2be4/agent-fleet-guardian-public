# 🐕‍🔥🔨 Agent Fleet Guardian

**Autonomous infrastructure support for AI agent orchestras**

> Cerberus audits. Hephaestus repairs. Your fleet stays alive.

---

## What is this?

Agent Fleet Guardian is a two-plane infrastructure support system for fleets of AI agents running on [OpenClaw](https://github.com/openclaw/openclaw). It solves a fundamental problem: **who watches the watchers?**

When you run 10, 20, or 50+ AI agents across multiple machines, things break. Containers OOM. Secrets leak into workspace files. Configs drift. Memory databases corrupt. Nobody notices until it's too late.

Fleet Guardian provides:
- **Audit Plane (Cerberus 🐕‍🔥)** — continuous security and architecture audits
- **Repair Plane (Hephaestus 🔨)** — diagnostics, fixes, and infrastructure maintenance

Both run as managed OpenClaw agents with their own SOUL, TOOLS, and cron schedules — zero human intervention required.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                   ORCHESTRATOR (L1)               │
│              (your main agent)             │
│                                                   │
│  ┌─────────────────┐   ┌──────────────────────┐  │
│  │  CERBERUS 🐕‍🔥    │   │  HEPHAESTUS 🔨       │  │
│  │  Audit Plane     │   │  Repair Plane        │  │
│  │                  │   │                       │  │
│  │  • Security scan │   │  • Container health   │  │
│  │  • Secret audit  │   │  • OOM detection      │  │
│  │  • Config drift  │   │  • Config repair      │  │
│  │  • Port exposure │   │  • Memory DB fixes    │  │
│  │  • Access review │   │  • Fleet healthcheck  │  │
│  │                  │   │                       │  │
│  │  READ ONLY       │──▶│  READ + REPAIR        │  │
│  │  Find → Report   │   │  Diagnose → Fix       │  │
│  └─────────────────┘   └──────────────────────┘  │
│           │                       │               │
│           ▼                       ▼               │
│    ┌──────────────────────────────────┐           │
│    │     NOTIFICATION CHANNEL         │           │
│    │  (Telegram / Discord / Slack)    │           │
│    └──────────────────────────────────┘           │
│                                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Mac #1 │ │ Mac #2 │ │ Mac #3 │ │ VPS    │    │
│  │ Docker │ │ Docker │ │ Docker │ │ Docker │    │
│  │ agents │ │ agents │ │ agents │ │ agents │    │
│  └────────┘ └────────┘ └────────┘ └────────┘    │
└──────────────────────────────────────────────────┘
```

## The Two Planes

### 🐕‍🔥 Cerberus — Audit Plane

Cerberus is the security officer. **Read-only. Never modifies anything.** Finds problems, classifies severity, reports to the orchestrator.

**What it audits:**
- Plaintext secrets in workspace files (SOUL.md, TOOLS.md, configs)
- Exposed ports and 0.0.0.0 binds
- SSH key and access hygiene
- Docker container security (privileged mode, volume mounts)
- Agent config drift (allowFrom, sendPolicy)
- Memory database integrity
- Cron job ownership and permissions

**Audit types:**

| Schedule | Type | Scope |
|----------|------|-------|
| Every 30 min | Quick ping | Container liveness, gateway reachability |
| Every hour | Pulse check | RAM/CPU/disk, container restarts |
| Every 4 hours | Full audit | Architecture, configs, security |
| Daily (07:00) | Deep report | Complete fleet health + recommendations |
| Weekly | Security scan | Secrets, access, exposure |

**Output format:**
```
🐕‍🔥 SECURITY AUDIT — 2026-03-15
🔴 CRITICAL: Plaintext DB password in SOUL.md (Athena agent)
🟡 WARNING: 9 cron jobs without explicit agentId
🟢 OK: All gateway binds are loopback
Recommendations: [actionable steps]
```

### 🔨 Hephaestus — Repair Plane

Hephaestus is the infrastructure engineer. **Diagnoses before fixing. Always reversible.** Follows the Cerberus audit trail and repairs what's broken.

**What it repairs:**
- OOM crash loops (detect → stop → set heap limits → restart)
- Broken container configs (missing env vars, corrupted paths)
- Gateway connectivity issues
- Memory database corruption (WAL mode, embeddings)
- Stale sessions and disk cleanup
- Docker image garbage collection
- Fleet-wide config synchronization

**Repair protocol:**
1. **Diagnose** — read logs, check status, understand root cause
2. **Plan** — propose fix with rollback strategy
3. **Execute** — minimal intervention, backup first
4. **Verify** — confirm fix works, no side effects
5. **Document** — post-mortem in memory

**Interaction with fleet:**
- **Preferred:** relay through L1 agents (they know their infra best)
- **Fallback:** direct SSH when L1 is down
- **Always:** notify L1 about any changes made

**Output format:**
```
🔨 REPAIR: Fleet OOM crash loop
Diagnosis: V8 heap unlimited, 5 workers cycling at 230% CPU
Fix: Recreated containers with NODE_OPTIONS=--max-old-space-size=900
Status: ✅ Load 7.0 → 1.9, all 11 workers stable
```

## Key Design Principles

### Separation of Concerns
Cerberus **finds**. Hephaestus **fixes**. They never overlap.

This separation prevents a common failure mode: the agent that finds the bug also "fixes" it in a way that masks the real problem.

### Read-Only Audit
Cerberus never modifies the system. This means:
- Audits can't break anything
- Results are always trustworthy (no observer effect)
- Security findings are credible (auditor ≠ implementer)

### Repair with Rollback
Hephaestus always:
- Takes backups before changes (`cp file file.bak.YYYYMMDD`)
- Uses `trash` over `rm` when possible
- Documents exact commands for rollback
- Verifies the fix actually worked

### L1-First Communication
When working on remote machines:
1. **Relay through L1** — the agent that lives on that machine knows best
2. **SSH fallback** — only when L1 is unreachable
3. **Always notify** — L1 must know about any changes to their infra

### Mandatory Security Review
Any deployment, config change, or new service must pass through Cerberus before going live. No exceptions.

## Setup

### Prerequisites
- [OpenClaw](https://github.com/openclaw/openclaw) installed
- SSH access to fleet machines (optional, for multi-machine setup)
- Telegram bot for notifications (optional)

### Quick Start

1. **Create agent directories:**
```bash
mkdir -p ~/.openclaw/agents/cerberus/agent
mkdir -p ~/.openclaw/agents/hephaestus/agent
```

2. **Copy SOUL.md, IDENTITY.md, TOOLS.md** from this repo into each agent directory.

3. **Add agents to your `openclaw.json`:**
```json
{
  "agents": {
    "list": [
      {
        "id": "cerberus",
        "name": "Cerberus",
        "workspace": "~/.openclaw/agents/cerberus/agent",
        "agentDir": "~/.openclaw/agents/cerberus/agent",
        "model": "anthropic/claude-sonnet-4-6",
        "memorySearch": { "enabled": false },
        "heartbeat": { "every": "0" },
        "tools": { "deny": ["gateway", "cron"] }
      },
      {
        "id": "hephaestus",
        "name": "Hephaestus",
        "workspace": "~/.openclaw/agents/hephaestus/agent",
        "agentDir": "~/.openclaw/agents/hephaestus/agent",
        "model": "anthropic/claude-sonnet-4-6",
        "memorySearch": { "enabled": false },
        "heartbeat": { "every": "0" }
      }
    ]
  }
}
```

4. **Set up cron schedules** (example):
```bash
# Cerberus: hourly audit
openclaw cron add --name "cerberus:hourly-audit" \
  --schedule '{"kind":"cron","expr":"0 * * * *"}' \
  --payload '{"kind":"agentTurn","message":"Run hourly audit on all fleet machines"}' \
  --sessionTarget isolated --agentId cerberus

# Hephaestus: daily self-check
openclaw cron add --name "hephaestus:daily-check" \
  --schedule '{"kind":"cron","expr":"30 7 * * *"}' \
  --payload '{"kind":"agentTurn","message":"Run daily infrastructure review"}' \
  --sessionTarget isolated --agentId hephaestus
```

5. **Restart gateway:**
```bash
openclaw gateway restart
```

### Multi-Machine Fleet Setup

For fleets with SSH access between machines, add connection details to Hephaestus TOOLS.md:

```markdown
## Fleet SSH
| Machine | IP | User | Role |
|---------|-----|------|------|
| local | 127.0.0.1 | admin | L1 main |
| worker-1 | 10.0.0.2 | agent | L2 workers |
| worker-2 | 10.0.0.3 | agent | L2 workers |
```

> ⚠️ Store SSH credentials in `.secrets/` files, never in TOOLS.md directly.

## Real-World Results

This system was battle-tested on a fleet of **35 AI agents across 3 Mac minis**:

- **Detected** OOM crash loops before they cascaded (5 workers, load 7.0)
- **Repaired** broken container env vars (slipped newlines in Docker run)
- **Found** 13 plaintext secrets across 4 workspace files
- **Identified** Telegram bot polling conflict (two processes, one bot)
- **Cleaned** 10+ GB of orphan Docker images
- **Isolated** 234 orphan memory chunks without agent_id
- **Reduced** fleet load from 7.0 → 1.9 in one repair cycle

## Customization

### Adapt SOUL.md to Your Fleet
The provided SOUL.md files are templates. Customize:
- Machine names and IPs in TOOLS.md
- Audit schedules to match your fleet size
- Notification channel (Telegram, Discord, Slack)
- Severity thresholds for your risk tolerance

### Extend Audit Checks
Add custom checks to Cerberus by updating its SOUL.md with your specific concerns:
- Compliance requirements
- Cost monitoring
- Model version tracking
- Uptime SLA enforcement

## Philosophy

> "One person must see the full picture, so they don't fix one thing while breaking another."

Infrastructure support for AI agents is not optional — it's the difference between a demo and a production system. Cerberus + Hephaestus give your fleet autonomous eyes and hands.

## 🧠 Semantic Memory Infrastructure

The project includes a production-ready **Graph-RAG memory layer** that any agent in your fleet can use.

### What it provides

- **SPO Knowledge Graph** — facts as (Subject → Predicate → Object) triples
- **Hybrid Search** — full-text (35%) + vector cosine similarity (65%)
- **Local Embeddings** — nomic-embed-text-v1.5-Q via fastembed (no API key needed)
- **Namespace Isolation** — each agent has its own memory space
- **HNSW Indexes** — fast approximate nearest neighbor via pgvector

### How it fits

```
┌──────────────────────────────────────────────────┐
│  Agent Memory Layers                             │
│                                                  │
│  L1: Working    │ Session context (OpenClaw)      │
│  L2: Episodic   │ MEMORY.md + daily notes         │
│  L3: Semantic   │ SPO Graph + pgvector ◄── THIS   │
│  L4: Procedural │ SOUL.md, skills                 │
└──────────────────────────────────────────────────┘
```

### Quick Start

```bash
cd memory-api
docker compose up -d
# API at http://localhost:18810

# Store a fact
curl -s http://localhost:18810/store -H "Content-Type: application/json" \
  -d '{"namespace":"main","subject":"Server","predicate":"has_issue","object":"OOM","content":"Server crashed due to OOM at 12:12 MSK"}'

# Search
curl -s http://localhost:18810/search -H "Content-Type: application/json" \
  -d '{"query":"server crashes","namespace":"main","limit":5}'
```

Full documentation: [`memory-api/MEMORY.md`](memory-api/MEMORY.md)

### Why Memory Matters for Infrastructure Agents

Cerberus and Hephaestus become dramatically more useful with persistent memory:
- **Cerberus** remembers past vulnerabilities, tracks whether they were fixed, detects regressions
- **Hephaestus** remembers past repairs, avoids repeating failed fixes, builds a repair knowledge base
- **Post-mortems** are stored as facts and searchable by future incidents
- **Fleet patterns** emerge over time (which containers crash most, which configs drift)

## License

MIT

## Credits

Built by [@born2be4](https://github.com/born2be4) as part of the OpenClaw agent ecosystem.

Inspired by the operational experience of running 35+ AI agents in production across multiple real-world organizations.
