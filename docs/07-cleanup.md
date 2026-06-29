# Cleanup

## Classification Buckets

| Bucket | Meaning | Action |
| --- | --- | --- |
| Keep active | Required by current profiles | Keep and monitor |
| Keep archived | Important but not active | Encrypt, archive, document |
| Transfer | Belongs to another person/team | Build handoff bundle |
| Delete later | Cache, duplicate, generated junk | Delete after approval |
| Unknown | Not understood | Do not delete |

## Cleanup Order

1. Stop duplicate pollers.
2. Disable unowned recurring jobs.
3. Remove caches and build outputs.
4. Archive legacy profiles.
5. Remove old runtimes only after the new server is stable.

## Token Budget Hygiene

Disable anything that reads, indexes, summarizes, or monitors in the background unless it has explicit owner approval.
