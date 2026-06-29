# Reference Architecture

```mermaid
flowchart TD
  human["Owner / approved users"] --> chat["Telegram, Slack, or another chat surface"]
  chat --> gateway["Hermes gateway per profile"]
  gateway --> infra["infra profile"]
  gateway --> comms["comms profile"]
  gateway --> analytics["analytics profile"]
  gateway --> content["content profile"]
  infra --> tools["server tools"]
  analytics --> data["approved data sources"]
  content --> media["approved media/workspaces"]
  comms --> memory["shared memory"]
  memory --> archives["encrypted archives"]
```

## Components

| Component | Responsibility |
| --- | --- |
| Server host | Always-on machine, remote access, backups, launch manager |
| Hermes runtime | Starts profile gateways and dispatches work |
| Profiles | Role-specific instructions, memory, tools, and chat policy |
| Shared memory | Calibrated cross-profile facts and operating rules |
| Legacy memory | Historical evidence imported from previous agents |
| Archives | Encrypted backups of sessions, memories, projects, and configs |

## Autostart

Use the native init system:

- macOS: `launchd` LaunchDaemons/LaunchAgents.
- Linux: `systemd` user or system services.

Each profile should restart automatically and write logs to a predictable path.
