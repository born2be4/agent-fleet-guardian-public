# TOOLS.md — Hephaestus

## Notification Channel
- TG: via dedicated bot (accountId=<your_bot>)
- Target: <owner_chat_id>

## SSH Fleet Access
| Machine | IP | User | Notes |
|---------|-----|------|-------|
| local | 127.0.0.1 | <user> | Main L1 host |
| worker-1 | <ip> | <user> | SSH key: ~/.ssh/<key> |

## Repair Commands
```bash
# Container management
docker restart <container>
docker stop <container>
docker rm -f <container> && docker run -d ...

# Gateway
openclaw gateway restart
openclaw status --deep

# Memory DB repair
sqlite3 ~/.openclaw/memory/main.sqlite "PRAGMA wal_checkpoint(TRUNCATE);"

# Disk cleanup
docker system prune -f
docker image prune -f
```

## Known Issues (update as you discover)
| Issue | Symptoms | Fix |
|-------|----------|-----|
| OOM crash loop | exitCode=137, high CPU | Set NODE_OPTIONS=--max-old-space-size=900 |
| Missing config | "Run openclaw setup" in logs | Check OPENCLAW_CONFIG_PATH env var |
| Telegram polling conflict | 409 getUpdates error | Stop duplicate bot process |
