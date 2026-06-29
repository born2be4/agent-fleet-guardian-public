#!/usr/bin/env bash
set -euo pipefail

profile_dir="${1:-}"
if [ -z "$profile_dir" ]; then
  echo "Usage: scripts/healthcheck.sh <profile-dir>" >&2
  exit 2
fi

fail=0
check_file() {
  if [ -f "$profile_dir/$1" ]; then
    echo "OK file: $1"
  else
    echo "MISS file: $1"
    fail=1
  fi
}

[ -d "$profile_dir" ] || { echo "Missing profile dir: $profile_dir"; exit 1; }
check_file AGENTS.md
check_file config.yaml

if [ -f "$profile_dir/gateway_state.json" ]; then
  echo "gateway_state.json: present"
  python3 - <<PY
import json
p='$profile_dir/gateway_state.json'
data=json.load(open(p))
print('gateway_state=', data.get('gateway_state'))
print('updated_at=', data.get('updated_at'))
print('platforms=', data.get('platforms'))
PY
else
  echo "gateway_state.json: not present yet"
fi

if [ -d "$profile_dir/logs" ]; then
  echo "logs dir: present"
  find "$profile_dir/logs" -type f -maxdepth 1 | tail -5
fi

exit "$fail"
