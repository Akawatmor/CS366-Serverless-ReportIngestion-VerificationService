#!/usr/bin/env bash
# ============================================================
# destroy.sh — Tear down all AWS resources
# ============================================================
# Usage:
#   ./scripts/destroy.sh                 # destroy with confirmation
#   ./scripts/destroy.sh --auto-approve  # skip confirmation
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TF_DIR="$PROJECT_ROOT/terraform"
LOGS_DIR="$PROJECT_ROOT/logs"
DEPLOY_RESULT_FILE="$PROJECT_ROOT/.deploy-result"

# ----------------------------------------------------------
# Setup logging
# ----------------------------------------------------------
mkdir -p "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/destroy-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo " Report Verify Service — Destroy"
echo "========================================"
echo "Timestamp: $(date -Iseconds)"
echo ""
echo "WARNING: This will delete ALL resources including DynamoDB tables and their data."
echo ""

cd "$TF_DIR"

if [[ "${1:-}" == "--auto-approve" ]]; then
    terraform destroy -auto-approve
else
    terraform destroy
fi

# ----------------------------------------------------------
# Cleanup deploy result (but keep logs for audit)
# ----------------------------------------------------------
if [[ -f "$DEPLOY_RESULT_FILE" ]]; then
    echo ""
    echo "[*] Removing deploy result file: $DEPLOY_RESULT_FILE"
    rm -f "$DEPLOY_RESULT_FILE"
fi

echo ""
echo "========================================"
echo " All resources destroyed."
echo "========================================"
echo "Timestamp: $(date -Iseconds)"
echo "Log file:  $LOG_FILE"
echo ""
echo "Note: Deploy logs are preserved in $LOGS_DIR/ for audit purposes."
echo "      To delete all logs: rm -rf $LOGS_DIR/"
