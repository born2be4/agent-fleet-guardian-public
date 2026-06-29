#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/create-profile.sh <profile-name>" >&2
  exit 2
fi

profile="$1"
root="${HERMES_HOME:-$HOME/.hermes}/profiles/$profile"
mkdir -p "$root/logs" "$root/memory" "$root/memories/shared" "$root/legacy"

cat > "$root/AGENTS.md" <<EOF
# Hermes profile: $profile

Role: describe this profile in one sentence.

Rules:
- Use the approved provider/model from config.yaml.
- Keep fallback_providers empty unless approved.
- Do not run passive jobs without explicit request.
- Do not print secrets.
EOF

cat > "$root/config.yaml" <<EOF
model:
  provider: openai-codex
  model: gpt-5.5
providers: {}
fallback_providers: []
profile:
  name: $profile
  passive_jobs_enabled: false
logging:
  level: INFO
EOF

echo "Created profile at $root"
