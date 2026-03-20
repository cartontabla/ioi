#!/bin/bash
# Deploy code to Raspberry Pi
# Usage: ./deploy.sh <pi_host> [<pi_user>]
# Example: ./deploy.sh 192.168.0.36 lino

set -e

PI_HOST=${1:-}
PI_USER=${2:-lino}

if [ -z "$PI_HOST" ]; then
    echo "Usage: ./deploy.sh <pi_host> [<pi_user>]"
    exit 1
fi

PI_SSH="${PI_USER}@${PI_HOST}"
REMOTE_DIR="/home/${PI_USER}/IOI"

echo "=== IOI Deploy → $PI_SSH:$REMOTE_DIR ==="

# 1. Check SSH
echo "[1/3] Checking SSH..."
if ! ssh -o ConnectTimeout=5 "$PI_SSH" "echo OK" > /dev/null 2>&1; then
    echo "Cannot connect to $PI_SSH"
    echo "Run: ssh-copy-id $PI_USER@$PI_HOST"
    exit 1
fi
echo "SSH OK"

# 2. Sync code (no venv, no cache, no local projects data)
echo "[2/3] Syncing code..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='projects/' \
    --exclude='.DS_Store' \
    . "$PI_SSH:$REMOTE_DIR/"
echo "Code synced"

# 3. Install Python deps with system Python (no venv on Pi)
echo "[3/3] Installing dependencies..."
ssh "$PI_SSH" "cd $REMOTE_DIR && pip3 install -r requirements.txt --break-system-packages -q 2>/dev/null || pip3 install -r requirements.txt -q"
echo "Dependencies OK"

echo ""
echo "Deploy complete. To start the backend on the Pi:"
echo "  ssh $PI_SSH"
echo "  cd $REMOTE_DIR && python3 run.py"
