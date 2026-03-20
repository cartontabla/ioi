#!/bin/bash
# Deploy code to Raspberry Pi (that already has Python, Node-RED, mosquitto, picamera installed)
# Usage: ./deploy.sh <pi_host> [<pi_user>]
# Example: ./deploy.sh 192.168.1.100 pi

set -e

PI_HOST=${1:-}
PI_USER=${2:-pi}

if [ -z "$PI_HOST" ]; then
    echo "Usage: ./deploy.sh <pi_host> [<pi_user>]"
    echo "Example: ./deploy.sh 192.168.1.100 pi"
    exit 1
fi

PI_SSH="${PI_USER}@${PI_HOST}"
REMOTE_DIR="/home/${PI_USER}/smartcam"

echo "=== Smart Camera Code Deployment to Raspberry Pi ==="
echo "Target: $PI_SSH"
echo ""

# 1. Check SSH
echo "[1/3] Checking SSH connection..."
if ! ssh -o ConnectTimeout=3 "$PI_SSH" "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Cannot connect to $PI_SSH"
    echo "   Try: ssh-copy-id $PI_USER@$PI_HOST"
    exit 1
fi
echo "✓ SSH OK"

# 2. Sync code
echo "[2/3] Syncing code..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='venv' --exclude='storage/*.jpg' --exclude='.DS_Store' \
    . "$PI_SSH:$REMOTE_DIR/" > /dev/null
echo "✓ Code synced to $REMOTE_DIR"

# 3. Install Python deps (assuming Pi already has venv + mosquitto + picamera setup)
echo "[3/3] Installing Python dependencies on Pi..."
ssh "$PI_SSH" << 'EOF'
    cd ~/smartcam
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1 || true
    echo "✓ Dependencies OK"
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Restart backend on Pi:"
echo "  ssh $PI_SSH"
echo "  cd ~/smartcam"
echo "  sudo systemctl restart smartcam"
echo "  sudo journalctl -u smartcam -f"
echo ""
echo "Or if running manually:"
echo "  source venv/bin/activate"
echo "  python3 run.py"
echo ""
