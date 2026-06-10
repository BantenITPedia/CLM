#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "$0")" && pwd)"
template_file="$repo_root/contract agreement/templates/distributor-template.html"

if [[ ! -f "$template_file" ]]; then
    echo "Template file not found: $template_file"
    exit 1
fi

last_hash=""
echo "Watching $template_file"
echo "Auto-sync target: DISTRIBUTOR"

while true; do
    current_hash="$(cksum "$template_file" | awk '{print $1":"$2}')"

    if [[ -z "$last_hash" ]]; then
        last_hash="$current_hash"
    elif [[ "$current_hash" != "$last_hash" ]]; then
        echo "Change detected, syncing..."
        "$repo_root/sync-template.sh" DISTRIBUTOR
        last_hash="$current_hash"
        echo "Sync complete."
    fi

    # Wait briefly without using external dependencies.
    read -r -t 1 _ || true
done