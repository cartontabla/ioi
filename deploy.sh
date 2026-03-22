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
SSH_KEY="$HOME/.ssh/id_ed25519_ioi"
SSH_OPTS="-i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no"

echo "=== IOI Deploy → $PI_SSH:$REMOTE_DIR ==="

# 1. Check SSH
echo "[1/4] Checking SSH..."
if ! ssh $SSH_OPTS "$PI_SSH" "echo OK" > /dev/null 2>&1; then
    echo "Cannot connect to $PI_SSH"
    echo "Run: ssh-copy-id -i $SSH_KEY $PI_SSH"
    exit 1
fi
echo "SSH OK"

# 2. Sync code (no venv, no cache, no local projects data)
echo "[2/4] Syncing code..."
rsync -avz --progress \
    -e "ssh $SSH_OPTS" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='projects/' \
    --exclude='.DS_Store' \
    . "$PI_SSH:$REMOTE_DIR/"
echo "Code synced"

# 3. Install Python deps with system Python (no venv on Pi)
echo "[3/4] Installing dependencies..."
ssh $SSH_OPTS "$PI_SSH" "cd $REMOTE_DIR && pip3 install -r requirements.txt --break-system-packages -q 2>/dev/null || pip3 install -r requirements.txt -q"
echo "Dependencies OK"

# 4. Install systemd service (first time) and restart backend
echo "[4/5] Restarting backend..."
ssh $SSH_OPTS "$PI_SSH" "
  sudo cp $REMOTE_DIR/ioi-backend.service /etc/systemd/system/ioi-backend.service
  sudo systemctl daemon-reload
  sudo systemctl enable ioi-backend
  sudo systemctl restart ioi-backend
"
sleep 5
curl -s --max-time 5 "http://${PI_HOST}:5001/api/health" > /dev/null && echo 'Backend OK' || echo 'Backend failed — check /tmp/ioi_backend.log on Pi'

# 5. Deploy Node-RED flow and restart
echo "[5/5] Deploying Node-RED flow..."
ssh $SSH_OPTS "$PI_SSH" "cp $REMOTE_DIR/node-red/flow.json /home/${PI_USER}/.node-red/flows.json && sudo systemctl restart nodered"
echo "Node-RED flow deployed and restarted"

echo ""
echo "Deploy complete. To start the backend on the Pi:"
echo "  ssh -i $SSH_KEY $PI_SSH"
echo "  cd $REMOTE_DIR && python3 run.py"
