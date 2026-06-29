#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
patterns='(BEGIN OPENSSH|BEGIN RSA|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|[0-9]{7,}:[A-Za-z0-9_-]{30,}|(BOT_TOKEN|TELEGRAM_TOKEN|API_HASH|API_KEY|SECRET|PASSWORD|SESSION)[A-Z0-9_]*=[^<[:space:]][^[:space:]]{8,})'

if grep -RInE "$patterns" "$root"   --exclude-dir=.git   --exclude='sanitize-scan.sh'   --exclude='*.html'   2>/dev/null; then
  echo "Potential secret pattern found. Review before sharing." >&2
  exit 1
fi

echo "No high-confidence secret patterns found. Still review manually before publishing."
