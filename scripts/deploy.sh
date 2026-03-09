#!/usr/bin/env bash
# ============================================================
# deploy.sh — Build Lambda packages + Terraform apply
# ============================================================
# Usage:
#   ./scripts/deploy.sh                    # deploy with defaults
#   ./scripts/deploy.sh --auto-approve     # skip confirmation
#   Reads .env file for GEMINI_API_KEY1, GEMINI_API_KEY2, etc.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
TF_DIR="$PROJECT_ROOT/terraform"
LOGS_DIR="$PROJECT_ROOT/logs"
DEPLOY_RESULT_FILE="$PROJECT_ROOT/.deploy-result"

AUTO_APPROVE=""
if [[ "${1:-}" == "--auto-approve" ]]; then
    AUTO_APPROVE="-auto-approve"
fi

# ----------------------------------------------------------
# Setup logging — tee to both stdout and log file
# ----------------------------------------------------------
mkdir -p "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo " Report Verify Service — Deploy"
echo "========================================"
echo "Timestamp:    $(date -Iseconds)"
echo "Project root: $PROJECT_ROOT"
echo "Log file:     $LOG_FILE"
echo ""

# ----------------------------------------------------------
# Load .env file
# ----------------------------------------------------------
ENV_FILE="$PROJECT_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
    echo "[*] Loading .env file..."
    set -a
    source "$ENV_FILE"
    set +a
    echo "  -> Loaded: $ENV_FILE"
else
    echo "[!] No .env file found at $ENV_FILE — using environment variables"
fi

# ----------------------------------------------------------
# Step 1: Clean build directory
# ----------------------------------------------------------
echo "[1/5] Cleaning build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ----------------------------------------------------------
# Step 2: Build Lambda package (source + dependencies)
# ----------------------------------------------------------
echo "[2/5] Building Lambda package..."
SRC_STAGING="$BUILD_DIR/lambda_src_staging"
mkdir -p "$SRC_STAGING"

# Install dependencies directly into staging dir
pip install \
    --target "$SRC_STAGING" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    -r "$PROJECT_ROOT/requirements.txt" \
    2>&1 | tail -5

# Fix google namespace packages (no __init__.py by default)
for dir in $(find "$SRC_STAGING" -type d -name "google"); do
    if [[ ! -f "$dir/__init__.py" ]]; then
        echo "# namespace package" > "$dir/__init__.py"
    fi
    for subdir in "$dir"/*/; do
        if [[ -d "$subdir" && ! -f "$subdir/__init__.py" ]]; then
            echo "# namespace package" > "$subdir/__init__.py"
        fi
    done
done

# Copy source code into staging
cp -r "$PROJECT_ROOT/src" "$SRC_STAGING/src"

# Create the source zip (includes everything Lambda needs)
cd "$SRC_STAGING"
zip -r9 "$BUILD_DIR/lambda_src.zip" . -x "*.pyc" "__pycache__/*" "*.egg-info/*" "*.dist-info/*" > /dev/null
echo "  -> Lambda package: $(du -sh "$BUILD_DIR/lambda_src.zip" | cut -f1)"
echo "  -> Uncompressed:   $(du -sh "$SRC_STAGING" | cut -f1)"

# Also create a minimal layer zip (empty placeholder for Terraform)
mkdir -p "$BUILD_DIR/lambda_layer_content/python"
echo "# placeholder" > "$BUILD_DIR/lambda_layer_content/python/__init__.py"
cd "$BUILD_DIR/lambda_layer_content"
zip -r9 "$BUILD_DIR/lambda_layer.zip" python/ > /dev/null

# ----------------------------------------------------------
# Step 3: Verify package
# ----------------------------------------------------------
echo "[3/5] Verifying Lambda package..."
echo "  -> google module: $(unzip -l "$BUILD_DIR/lambda_src.zip" | grep -c "google/")"
echo "  -> src module:    $(unzip -l "$BUILD_DIR/lambda_src.zip" | grep -c "src/")"

# ----------------------------------------------------------
# Step 4: Terraform init
# ----------------------------------------------------------
echo "[4/5] Initializing Terraform..."
cd "$TF_DIR"
terraform init -input=false

# ----------------------------------------------------------
# Step 5: Terraform apply
# ----------------------------------------------------------
echo "[5/5] Applying Terraform..."

# Build -var flags for Gemini API keys
TF_VARS=""
for i in $(seq 1 10); do
    VAR_NAME="GEMINI_API_KEY${i}"
    VAR_VALUE="${!VAR_NAME:-}"
    if [[ -n "$VAR_VALUE" ]]; then
        TF_VARS="$TF_VARS -var=gemini_api_key${i}=${VAR_VALUE}"
        echo "  -> Found $VAR_NAME"
    fi
done

# Gemini model fallbacks
if [[ -n "${GEMINI_MODEL_FALLBACKS:-}" ]]; then
    TF_VARS="$TF_VARS -var=gemini_model_fallbacks=${GEMINI_MODEL_FALLBACKS}"
fi

if [[ -n "$AUTO_APPROVE" ]]; then
    terraform apply $AUTO_APPROVE $TF_VARS
else
    terraform plan $TF_VARS
    echo ""
    read -p "Apply these changes? (yes/no): " confirm
    if [[ "$confirm" == "yes" ]]; then
        terraform apply -auto-approve $TF_VARS
    else
        echo "Deployment cancelled."
        exit 0
    fi
fi

# ----------------------------------------------------------
# Output
# ----------------------------------------------------------
echo ""
echo "========================================"
echo " Deployment Complete!"
echo "========================================"
echo " $(date -Iseconds)"
echo ""

# Display website URLs prominently
WEBSITE_URL=$(terraform output -raw website_url 2>/dev/null || echo "")
DASHBOARD_URL=$(terraform output -raw dashboard_url 2>/dev/null || echo "")
API_URL=$(terraform output -raw api_url 2>/dev/null || echo "")

if [[ -n "$WEBSITE_URL" ]]; then
    echo "  Landing Page:   $WEBSITE_URL"
fi
if [[ -n "$DASHBOARD_URL" ]]; then
    echo "  Dashboard:      $DASHBOARD_URL"
fi
if [[ -n "$API_URL" ]]; then
    echo "  API Base URL:   $API_URL"
fi
echo "  API Key:        (sensitive — run: terraform output -raw api_key)"
echo ""

# Save full outputs to .deploy-result for quick reference
{
    echo "# ================================================"
    echo "# Deploy Result — $(date -Iseconds)"
    echo "# Re-run: ./scripts/deploy.sh --auto-approve"
    echo "# ================================================"
    echo ""
    terraform output 2>/dev/null
} > "$DEPLOY_RESULT_FILE"
echo "  Saved to:       $DEPLOY_RESULT_FILE"

# Full outputs on screen
echo ""
terraform output -json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('--- All Outputs ---')
for key, val in data.items():
    v = val.get('value', '')
    if isinstance(v, dict):
        print(f'{key}:')
        for k2, v2 in v.items():
            print(f'  {k2}: {v2}')
    elif val.get('sensitive'):
        print(f'{key}: (sensitive — use: terraform output -raw {key})')
    else:
        print(f'{key}: {v}')
print()
" 2>/dev/null || terraform output

echo ""
echo "Log file: $LOG_FILE"
