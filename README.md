# Personal Hermes Agent Server Template

A privacy-first template for setting up a personal or team Mac/Linux server for AI agents powered by Hermes profiles.

This repository is intentionally anonymized. It contains no private hostnames, no Telegram IDs, no tokens, no session files, no internal project names, and no user-specific memory.

## What This Helps You Build

A small always-on machine that can run several personal/work agents with:

- one profile per agent role;
- explicit model/provider lock;
- no silent fallback providers by default;
- safe Telegram or chat integrations;
- preserved memory and project archives;
- launchd/systemd autostart;
- repeatable health checks;
- a cleanup and migration process that does not lose memory.

## Recommended Roles

| Profile | Purpose |
| --- | --- |
| `infra` | server setup, repairs, deployment, diagnostics |
| `comms` | communication, approvals, summaries, stakeholder updates |
| `analytics` | reports, spreadsheets, metrics, numerical checks |
| `content` | PR, social posts, channel/group content, media handoff |

Rename these profiles for your organization, but keep one clear responsibility per profile.

## Quick Start

1. Read `docs/00-principles.md`.
2. Fill `config/server.example.env` and copy it outside git as `.env`.
3. Create profiles from `examples/profiles/`.
4. Install launch agents from `examples/launchd/` or systemd units from `examples/systemd/`.
5. Run `scripts/healthcheck.sh`.
6. Run `scripts/sanitize-scan.sh` before sharing any repo or archive.

## Repository Map

- `docs/00-principles.md` - operating rules and privacy model.
- `docs/01-architecture.md` - reference architecture.
- `docs/02-installation.md` - setup flow for a new server.
- `docs/03-profiles.md` - how to design agent profiles.
- `docs/04-operations.md` - health checks, restarts, logs, autostart.
- `docs/05-security.md` - secrets, Telegram, auth, network, backups.
- `docs/06-migration.md` - preserving memories and projects.
- `docs/07-cleanup.md` - deciding what to keep, archive, transfer, delete.
- `examples/` - profile, config, launchd, and systemd examples.
- `scripts/` - small helper scripts that are safe to inspect and adapt.
- `presentations/server-template.html` - shareable HTML overview.

## Non-Goals

This template does not ship private credentials, does not prescribe one vendor account, and does not include a raw memory dump. It is a structure for building your own server safely.
