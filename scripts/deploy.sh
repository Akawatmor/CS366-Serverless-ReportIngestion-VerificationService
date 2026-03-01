#!/usr/bin/env bash
# ============================================================
# deploy.sh — Build Lambda packages + Terraform apply
# ============================================================
# Usage:
#   ./scripts/deploy.sh                    # deploy with defaults
#   ./scripts/deploy.sh --auto-approve     # skip confirmation
#   GEMINI_API_KEY=xxx ./scripts/deploy.sh # pass API key
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
TF_DIR="$PROJECT_ROOT/terraform"

AUTO_APPROVE=""
if [[ "${1:-}" == "--auto-approve" ]]; then
    AUTO_APPROVE="-auto-approve"
fi

echo "========================================"
echo " Report Verify Service — Deploy"
echo "========================================"
echo "Project root: $PROJECT_ROOT"
echo ""

# ----------------------------------------------------------
# Step 1: Clean build directory
# ----------------------------------------------------------
echo "[1/5] Cleaning build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ----------------------------------------------------------
# Step 2: Build Lambda Layer (dependencies)
# ----------------------------------------------------------
echo "[2/5] Building Lambda Layer..."
LAYER_DIR="$BUILD_DIR/lambda_layer_content/python"
mkdir -p "$LAYER_DIR"

pip install \
    --target "$LAYER_DIR" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    -r "$PROJECT_ROOT/requirements.txt" \
    2>&1 | tail -5

# Create layer zip
cd "$BUILD_DIR/lambda_layer_content"
zip -r9 "$BUILD_DIR/lambda_layer.zip" python/ -x "*.pyc" "__pycache__/*" > /dev/null
echo "  -> Lambda layer: $(du -sh "$BUILD_DIR/lambda_layer.zip" | cut -f1)"

# ----------------------------------------------------------
# Step 3: Package Lambda source code
# ----------------------------------------------------------
echo "[3/5] Packaging Lambda source..."
cd "$PROJECT_ROOT/src"
zip -r9 "$BUILD_DIR/lambda_src.zip" . -x "*.pyc" "__pycache__/*" "*.egg-info/*" > /dev/null
echo "  -> Lambda source: $(du -sh "$BUILD_DIR/lambda_src.zip" | cut -f1)"

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

# Pass Gemini API key if set in environment
TF_VARS=""
if [[ -n "${GEMINI_API_KEY:-}" ]]; then
    TF_VARS="-var=gemini_api_key=$GEMINI_API_KEY"
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
terraform output -json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print()
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
