#!/bin/bash
# NetWatch AI - GNS3 Ubuntu deployment helper
set -e

APP_DIR="/opt/netwatch"
BACKEND="$APP_DIR/backend"
FRONTEND="$APP_DIR/frontend"

echo "=== NetWatch AI GNS3 Deployment ==="

# Install dependencies
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv nodejs npm iputils-ping

# Backend setup
cd "$BACKEND"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env — edit GNS3_PROJECT_ID and SECRET_KEY before starting"
fi

python seed.py

# Frontend build
cd "$FRONTEND"
npm install
npm run build

# Systemd service (optional)
cat << 'UNIT' | sudo tee /etc/systemd/system/netwatch.service
[Unit]
Description=NetWatch AI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/netwatch/backend
Environment=PATH=/opt/netwatch/backend/venv/bin
ExecStart=/opt/netwatch/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable netwatch
sudo systemctl start netwatch

echo ""
echo "Backend running on http://0.0.0.0:8000"
echo "Serve frontend: cd $FRONTEND && npx serve dist -l 5173"
echo "Default login: admin / admin123"
