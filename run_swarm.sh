#!/usr/bin/env bash
# Dreyer AI Studio — Ruflo Testsvärm wrapper
# Läser ANTHROPIC_API_KEY från .streamlit/secrets.toml om env-var saknas
# Användning: bash run_swarm.sh --variant "Svara på: {input}" --variant-id v1 --workers 10

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS="$SCRIPT_DIR/.streamlit/secrets.toml"

# Ladda ANTHROPIC_API_KEY från secrets.toml om den inte redan är satt
if [[ -z "${ANTHROPIC_API_KEY:-}" && -f "$SECRETS" ]]; then
  export ANTHROPIC_API_KEY
  ANTHROPIC_API_KEY=$(grep -E '^ANTHROPIC_API_KEY' "$SECRETS" | head -1 | sed "s/.*=[ ]*['\"]\\?//;s/['\"][ ]*$//")
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "❌ ANTHROPIC_API_KEY saknas. Lägg till i .streamlit/secrets.toml eller exportera den." >&2
  exit 1
fi

cd "$SCRIPT_DIR"
exec python3 -m agents.swarm_runner "$@"
