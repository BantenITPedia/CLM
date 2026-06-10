#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "$0")" && pwd)"

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 CONTRACT_TYPE [HOST_HTML_FILE]"
    echo "Example: $0 DISTRIBUTOR"
    echo "Example: $0 GENERAL_TRADE /opt/clm/contract agreement/templates/general-trade-template.html"
    exit 1
fi

contract_type="${1^^}"
host_file="${2:-}"

case "$contract_type" in
    DISTRIBUTOR)
        default_host_file="$repo_root/contract agreement/templates/distributor-template.html"
        container_file="/app/contract agreement/templates/distributor-template.html"
        ;;
    GENERAL_TRADE)
        default_host_file="$repo_root/contract agreement/templates/general-trade-template.html"
        container_file="/app/contract agreement/templates/general-trade-template.html"
        ;;
    GENERAL_TRADE_PREMIUM)
        default_host_file="$repo_root/contract agreement/templates/general-trade-premium-template.html"
        container_file="/app/contract agreement/templates/general-trade-premium-template.html"
        ;;
    *)
        default_host_file=""
        container_file=""
        ;;
esac

if [[ -z "$host_file" ]]; then
    if [[ -z "$default_host_file" ]]; then
        echo "No default file mapping for $contract_type. Pass the file path explicitly."
        exit 1
    fi
    host_file="$default_host_file"
fi

if [[ ! -f "$host_file" ]]; then
    echo "File not found: $host_file"
    exit 1
fi

if [[ -z "$container_file" || "$host_file" != "$default_host_file" ]]; then
    container_file="/tmp/${contract_type,,}-template-sync.html"
fi

container_dir="$(dirname "$container_file")"
docker exec clm-app mkdir -p "$container_dir"
docker cp "$host_file" "clm-app:$container_file"
docker exec clm-app python manage.py shell -c "
from pathlib import Path
from contracts.models import ContractTemplate, ContractTypeDefinition

contract_type_code = '${contract_type}'
source_path = Path(r'''${container_file}''')
type_def = ContractTypeDefinition.objects.filter(code=contract_type_code, active=True).first()
if not type_def:
    raise SystemExit(f\"Contract type not found or inactive: {contract_type_code}\")

template = ContractTemplate.objects.filter(contract_type=type_def, active=True).order_by('-version').first()
if not template:
    raise SystemExit(f\"No active template found for: {contract_type_code}\")

content = source_path.read_text(encoding='utf-8')
if not content.strip():
    raise SystemExit(f\"Template file is empty: {source_path}\")

template.content = content
template.save(update_fields=['content'])
print('Template synced successfully')
print(f'Contract Type: {type_def.code}')
print(f'Template ID: {template.id}')
print(f'Template Name: {template.name}')
print(f'Version: {template.version}')
print(f'Source File: {source_path}')
print(f'Content Length: {len(content)} characters')
"

echo "Synced $contract_type from $host_file"