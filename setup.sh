#!/bin/bash
# Quick setup + deploy to Raspberry Pi (that already has picamera, mosquitto, node-red installed)

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Smart Camera - Setup & Deploy (Mac → Raspberry Pi)      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Step 0: Gather Pi info
echo "Configure your Raspberry Pi"
echo "─────────────────────────────────────────────────"
read -p "Pi IP/hostname (e.g., 192.168.1.100 or pi.local): " PI_HOST
read -p "Pi username [pi]: " PI_USER
PI_USER=${PI_USER:-pi}
PI_SSH="${PI_USER}@${PI_HOST}"
echo ""

# Step 1: Local setup on Mac
echo "Setting up local development environment"
echo "─────────────────────────────────────────────────"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    echo "✓ venv created"
else
    . venv/bin/activate
    echo "✓ venv exists"
fi
echo ""

# Step 2: Quick local test
echo "Quick local test (OpenCV fallback)"
echo "─────────────────────────────────────────────────"
echo "Starting backend for 5 seconds..."
timeout 5 python3 run.py 2>&1 | head -5 &
sleep 2

if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✓ Backend OK at http://localhost:5000"
else
    echo "⚠ Backend not responding (MQTT broker issue? Ignore for now)"
fi
wait 2>/dev/null || true
echo ""

# Step 3: Deploy to Pi
echo "Deploying to Raspberry Pi"
echo "─────────────────────────────────────────────────"
if ! ssh -o ConnectTimeout=3 "$PI_SSH" "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Cannot reach $PI_SSH"
    echo "   Fix SSH first: ssh-copy-id $PI_USER@$PI_HOST"
    exit 1
fi

./deploy.sh "$PI_HOST" "$PI_USER"
echo ""

# Step 4: Summary
echo "Setup complete! ✓"
echo ""
echo "Next steps (SSH into your Pi):"
echo "  ssh $PI_SSH"
echo "  cd ~/smartcam"
echo ""
echo "Then run one of:"
echo ""
echo "  # Manual (for testing)"
echo "  source venv/bin/activate"
echo "  python3 run.py"
echo ""
echo "  # As service (for production)"
echo "  sudo systemctl restart smartcam"
echo "  sudo systemctl status smartcam"
echo ""
echo "Verify in another terminal:"
echo "  curl http://$PI_HOST:5000/api/health"
echo ""

