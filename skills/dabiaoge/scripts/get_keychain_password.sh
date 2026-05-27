#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:-freshos-dabiaoge}"
ACCOUNT="${2:-kang}"

security find-generic-password -s "$SERVICE" -a "$ACCOUNT" -w
