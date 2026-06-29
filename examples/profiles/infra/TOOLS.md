# Tools - infra

Allowed by default:

- shell diagnostics;
- git inside approved repositories;
- launchd/systemd status and restart commands;
- log reading with redaction;
- archive inventory.

Denied by default:

- reading secret files unless the task requires it;
- printing secret values;
- deleting unclassified data;
- changing provider/model fallback rules without approval.
