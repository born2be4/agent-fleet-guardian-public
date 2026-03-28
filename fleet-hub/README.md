# 🌐 Fleet Message Hub (n8n-bridge v2)

**Central message bus for AI agent fleets running on OpenClaw.**

One endpoint. Any agent. Any machine. Automatic routing.

---

## Problem

When your fleet grows to 40+ agents across 4+ machines, inter-agent communication becomes a mess:
- Local agents use `sessions_send`
- Remote L1 agents need SSH + `openclaw cron`
- Docker workers need SSH + `docker exec` + `openclaw cron`
- Every agent needs to know the topology

Fleet Hub solves this: **agents know one URL and one agent ID — Hub handles the rest.**

## How It Works

```
┌──────────────┐     POST /message      ┌──────────────────┐
│   Agent A    │ ──────────────────────▶ │    Fleet Hub     │
│  (anywhere)  │                         │   :5679          │
└──────────────┘                         │                  │
                                         │  ┌────────────┐  │
                                         │  │  Registry   │  │
                                         │  │  41 agents  │  │
                                         │  │  4 machines │  │
                                         │  └────────────┘  │
                                         │        │         │
                                         │   Route by type  │
                                         └────────┬─────────┘
                           ┌──────────────────────┼──────────────────────┐
                           ▼                      ▼                      ▼
                    ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
                    │ Local Agent │      │  Remote L1   │      │ Remote Docker│
                    │ cron add    │      │ SSH → cron   │      │ SSH → docker │
                    │ --agent X   │      │   add        │      │ exec → cron  │
                    └─────────────┘      └──────────────┘      └──────────────┘
```

### Delivery Flow
1. Agent sends `POST /message` with `target` agent ID
2. Hub looks up target in registry → determines mac, type (managed/L1/docker), container name
3. Hub routes automatically:
   - **Local managed** → `openclaw cron add --agent X --system-event "..." --at +1m --delete-after-run`
   - **Remote L1** → SSH to host → `openclaw cron add ...`
   - **Remote Docker** → SSH to host → `docker exec <container> openclaw cron add ...`
4. Target agent receives message in ~1 minute via one-shot cron job
5. Hub logs the delivery attempt (sender, target, status, method)

### Why cron add?
OpenClaw gateways don't expose a direct "inject message" HTTP API. But `openclaw cron add --at <ISO> --delete-after-run` creates a one-shot job that fires once and self-destructs. This is the most reliable cross-gateway delivery mechanism that works both inside Docker containers and on bare host gateways.

## API

### POST /message — Send to any agent
```bash
curl -s -X POST http://localhost:5679/message \
  -H "Content-Type: application/json" \
  -d '{
    "target": "rizz-marketing",
    "message": "check campaign performance",
    "sender": "cerberus"
  }'
```
```json
{"status": "delivered", "target": "rizz-marketing", "method": "ssh-docker-cron"}
```

### POST /broadcast — Send to group or list
```bash
# By group
curl -s -X POST http://localhost:5679/broadcast \
  -H "Content-Type: application/json" \
  -d '{"group": "rizz", "message": "config update", "sender": "hephaestus"}'

# By explicit list
curl -s -X POST http://localhost:5679/broadcast \
  -H "Content-Type: application/json" \
  -d '{"targets": ["cerberus", "iris", "athena"], "message": "briefing at 10", "sender": "main"}'
```

Built-in groups: `local`, `rizz`, `semily`, `stas`, `all-l1`, `all-docker`, `all`

### POST /status — Check agent health
```bash
# Single agent
curl -s -X POST http://localhost:5679/status \
  -d '{"target": "semily-cfo"}'

# Whole group
curl -s -X POST http://localhost:5679/status \
  -d '{"group": "semily"}'
```
```json
{"agent": "semily-cfo", "mac": "semily", "status": "up", "detail": "running"}
```

### POST /relay — SSH command on remote mac
```bash
curl -s -X POST http://localhost:5679/relay \
  -d '{"host": "rizz", "command": "docker stats --no-stream"}'
```

### GET /health — Service health
```json
{"status": "ok", "version": 2, "agents": 41, "macs": ["local", "rizz", "semily", "stas"]}
```

### GET /registry — Full agent registry
Returns all agents with their mac, type, session key, container name.

### GET /logs?limit=N — Recent message log
Returns last N messages with timestamp, sender, target, status, method.

## Agent Registry

Hub maintains a built-in registry of all fleet agents:

| Type | Location | Delivery | Example |
|------|----------|----------|---------|
| `managed` | Local OpenClaw agents | `openclaw cron add --agent X` | hephaestus, cerberus, iris |
| `l1` | Remote host gateway | SSH → `openclaw cron add` | sigma (Rizz), ceo-semily |
| `docker` | Remote Docker worker | SSH → `docker exec` → `cron add` | rizz-marketing, semily-cfo |

### Agent ID Convention
- Local: `agent_name` (e.g., `cerberus`, `iris`)
- Remote L1: `name` (e.g., `sigma`, `ceo-semily`)
- Remote Docker: `mac-role` (e.g., `rizz-marketing`, `semily-cfo`, `stas-trust`)

## Setup

### Prerequisites
- Python 3.8+
- SSH key access to remote macs
- OpenClaw installed on all machines

### Install
```bash
# Copy the bridge script
cp fleet-hub/n8n-bridge.py ~/.openclaw/scripts/n8n-bridge.py

# Create LaunchAgent (macOS)
cat > ~/Library/LaunchAgents/com.openclaw.n8n-bridge.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.n8n-bridge</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/python3</string>
        <string>~/.openclaw/scripts/n8n-bridge.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/n8n-bridge-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/n8n-bridge-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

# Load
launchctl load ~/Library/LaunchAgents/com.openclaw.n8n-bridge.plist
```

### Configure
Edit `AGENT_REGISTRY` and `SSH_MAP` in `n8n-bridge.py` to match your fleet topology.

### Agent Integration
Add to each agent's SOUL.md:
```markdown
## Fleet Message Hub
For inter-agent communication, use the Fleet Hub.
POST http://<hub-ip>:5679/message with {"target":"<agent_id>","message":"...","sender":"<my_id>"}
```

## Architecture Notes

- **Stateless** — no database, message log is in-memory (last 500 entries)
- **No auth** — designed for trusted LAN/Tailscale networks
- **Fault-tolerant delivery** — if SSH fails, Hub reports `failed` with details
- **Self-cleaning** — all injected cron jobs use `--delete-after-run`
- **~1 min latency** — acceptable for async agent-to-agent communication
- **Zero dependencies** — pure Python stdlib, no pip packages

## Relation to Other Components

| Component | Role |
|-----------|------|
| **Fleet Hub** | Message routing between any agents |
| **Cerberus** | Security audits, sends tasks to Hephaestus via Hub |
| **Hephaestus** | Infrastructure repair, receives tasks via Hub |
| **Memory API** | Shared Brain for fleet knowledge (separate service) |
| **n8n** | Business automation workflows (optional, Docker) |

## License

MIT — same as parent repo.
