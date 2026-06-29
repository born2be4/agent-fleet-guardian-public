# Installation

## 1. Choose A Host

Recommended minimum:

- Apple Silicon Mac mini, laptop, or Linux VPS/mini PC.
- 16 GB RAM or more.
- SSD with enough room for memories, logs, and archives.
- Stable network route for remote administration.
- Full-disk encryption if the machine stores private data.

## 2. Prepare Directories

```bash
mkdir -p "$HOME/.hermes/profiles"
mkdir -p "$HOME/agent-server/archives"
mkdir -p "$HOME/agent-server/shared-memory"
mkdir -p "$HOME/agent-server/logs"
```

## 3. Install Hermes

Follow the official Hermes installation guide for your platform:

```text
https://hermes-agent.nousresearch.com/
```

Keep runtime code separate from profile data. A common layout is:

```text
~/.hermes/hermes-agent/        # runtime clone/install
~/.hermes/profiles/<profile>/  # profile state, config, memory, logs
~/agent-server/                # local project archives and shared docs
```

## 4. Create Profiles

Copy one example profile:

```bash
cp -R examples/profiles/infra "$HOME/.hermes/profiles/infra"
```

Then edit:

- `AGENTS.md`
- `IDENTITY.md`
- `SOUL.md`
- `TOOLS.md`
- `config.yaml`
- `.env` outside git

## 5. Configure Autostart

macOS:

```bash
cp examples/launchd/com.example.hermes.profile.plist ~/Library/LaunchAgents/com.example.hermes.infra.plist
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.example.hermes.infra.plist
launchctl kickstart -k "gui/$(id -u)/com.example.hermes.infra"
```

Linux:

```bash
mkdir -p ~/.config/systemd/user
cp examples/systemd/hermes-profile.service ~/.config/systemd/user/hermes-infra.service
systemctl --user daemon-reload
systemctl --user enable --now hermes-infra.service
```

## 6. Verify

```bash
scripts/healthcheck.sh "$HOME/.hermes/profiles/infra"
```

A setup is not done until the profile starts, logs are readable, chat integration is connected, and a live smoke test passes.
