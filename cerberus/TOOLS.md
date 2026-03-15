# TOOLS.md — Cerberus

## Notification Channel
- TG: via dedicated bot (accountId=<your_bot>)
- Target: <owner_chat_id>

## SSH Fleet Access (read-only)
| Machine | IP | User | Notes |
|---------|-----|------|-------|
| local | 127.0.0.1 | <user> | Main L1 host |
| worker-1 | <ip> | <user> | SSH key: ~/.ssh/<key> |

## Audit Commands
```bash
# OpenClaw status
openclaw status --deep
openclaw security audit --deep

# Docker
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}"
docker stats --no-stream

# Memory DB
sqlite3 ~/.openclaw/memory/main.sqlite "PRAGMA journal_mode;"
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT count(*) FROM chunks;"

# Secrets scan
grep -rn "sk-ant\|sk-proj\|Bearer\|password\|secret" ~/.openclaw/workspace/ --include="*.md"
```
