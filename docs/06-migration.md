# Migration

## Migration Flow

1. Inventory current agents and profiles.
2. Freeze passive jobs.
3. Back up memories, projects, sessions, and config.
4. Classify data into keep, archive, transfer, delete, unknown.
5. Create new Hermes profiles.
6. Import calibrated memory first, legacy memory second.
7. Run live smoke tests.
8. Disable duplicate pollers.
9. Document the new source of truth.

## Preserve-First Checklist

- `AGENTS.md`, `IDENTITY.md`, `SOUL.md`, `TOOLS.md`.
- `memory/` or equivalent knowledge directories.
- profile `config.yaml` without secrets.
- encrypted `.env` and session backups.
- project workspaces and deliverables.
- launchd/systemd units.
- repair logs and runbooks.

## What To Avoid

- Copying raw old memory directly into the prompt without calibration.
- Running old and new Telegram pollers for the same token.
- Keeping fallback providers from an old setup.
- Leaving background indexers enabled during migration.
- Deleting old data before restore is tested.
