#!/bin/bash
# Named entrypoint for the isolated stock-analysis harness.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/harness-run.sh" "$@"
