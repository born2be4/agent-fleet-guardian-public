# Security

## Do Not Commit

- `.env` files.
- Telegram bot tokens.
- Telegram `.session` files.
- API keys or provider tokens.
- OAuth credential JSON.
- Private SSH keys.
- TOTP seeds or generated codes.
- Raw logs containing private conversations.
- Full local caches.

## Recommended `.gitignore`

This template includes a defensive `.gitignore`. Keep it strict and add new secret patterns before importing old data.

## Chat Access

Use allowlists. A profile should know:

- who may DM it;
- which groups it may read;
- whether it may answer without a mention;
- whether it may send files/media;
- where live smoke tests happen.

## Backups

Use encrypted archives for:

- profile directories;
- memories;
- session files;
- project workspaces;
- launch configs;
- dependency lockfiles.

Test restore before deleting originals.

## Network

Document the expected network route. If your environment requires a VPN or proxy, make it explicit:

- name of the approved client;
- autostart policy;
- health check command;
- what must not run in parallel.
