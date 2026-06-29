#!/usr/bin/env bash
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
AGENT_SERVER_HOME="${AGENT_SERVER_HOME:-$HOME/agent-server}"

mkdir -p "$HERMES_HOME/profiles"
mkdir -p "$AGENT_SERVER_HOME/archives" "$AGENT_SERVER_HOME/shared-memory" "$AGENT_SERVER_HOME/logs"

echo "Created: $HERMES_HOME/profiles"
echo "Created: $AGENT_SERVER_HOME"
echo "Next: install Hermes runtime from https://hermes-agent.nousresearch.com/"
