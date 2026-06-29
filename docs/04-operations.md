# Operations

## Health Check

```bash
scripts/healthcheck.sh "$HOME/.hermes/profiles/infra"
```

The script checks:

- profile directory exists;
- config files exist;
- `gateway_state.json`, if present;
- recent logs, if present;
- obvious secret leaks in committed files.

## Restart macOS LaunchAgent

```bash
label=com.example.hermes.infra
launchctl kickstart -k "gui/$(id -u)/$label"
```

For LaunchDaemons:

```bash
sudo launchctl kickstart -k system/com.example.hermes.infra
```

## Restart Linux systemd User Service

```bash
systemctl --user restart hermes-infra.service
systemctl --user status hermes-infra.service --no-pager
journalctl --user -u hermes-infra.service -n 100 --no-pager
```

## Log Policy

Logs are operational evidence. They are not public artifacts. Before sharing logs, redact:

- tokens;
- chat IDs if private;
- phone numbers;
- session strings;
- private messages;
- API keys and OAuth material.

## Repair Report Format

```markdown
## YYYY-MM-DD - Profile repair

- Target profile:
- Symptom:
- Root cause:
- Change made:
- Verification:
- Secrets touched: no / yes, redacted
- Follow-up:
```
