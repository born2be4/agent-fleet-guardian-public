# Profiles

## Profile Contract

Every profile should answer these questions:

| Question | File |
| --- | --- |
| Who am I? | `IDENTITY.md` |
| How should I behave? | `SOUL.md` |
| What can I use? | `TOOLS.md` |
| What is my current runtime config? | `config.yaml` |
| What shared facts should I load first? | `memories/shared/INDEX.md` |
| What historical data is evidence only? | `legacy/` |

## Model Lock Example

```yaml
model:
  provider: openai-codex
  model: gpt-5.5
providers: {}
fallback_providers: []
```

Replace provider/model with your approved route. Keep fallback empty until explicitly approved.

## Tool Policy

Start narrow:

- allow read-only shell for diagnostics;
- allow git only inside approved workspaces;
- allow network only when the profile needs it;
- deny access to secrets by default;
- add write permissions per profile, not globally.

## Shared Memory Priority

1. Current profile files.
2. Shared memory canon.
3. Imported legacy memory.
4. Raw logs and archives.

If old memory conflicts with current config, current config wins.
