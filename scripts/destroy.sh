#!/usr/bin/env bash
# ============================================================
# destroy.sh — Tear down all AWS resources
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$(dirname "$SCRIPT_DIR")/terraform"

echo "========================================"
echo " Report Verify Service — Destroy"
echo "========================================"
echo ""
echo "WARNING: This will delete ALL resources including DynamoDB tables and their data."
echo ""

cd "$TF_DIR"

if [[ "${1:-}" == "--auto-approve" ]]; then
    terraform destroy -auto-approve
else
    terraform destroy
fi

echo ""
echo "All resources destroyed."
