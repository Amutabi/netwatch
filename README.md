# NetWatch AI

Network monitoring and configuration chatbot for **GNS3 lab environments**. Monitors device metrics, detects faults, provides AI-powered recommendations, and executes SSH configuration changes after admin approval.

## Features

| Feature | Description |
|---------|-------------|
| **Live monitoring** | ICMP ping every 30s — latency, reachability |
| **Fault detection** | Rule-based alerts with recommendations |
| **AI chatbot** | Plain English: status queries, config requests |
| **Admin-gated SSH** | Netmiko execution after approval |
| **GNS3 sync** | Auto-discover/remove devices from topology |
| **Reports** | Downloadable PDF and CSV |
| **Audit logs** | Full action history + conversation memory |
| **Live alerts** | WebSocket push to dashboard |

## Architecture

```
Browser → React SPA → FastAPI → [Monitor | SSH | AI | GNS3 Sync] → Network Devices
                              ↘ PostgreSQL/SQLite
                              ↘ WebSocket (alerts)
```

See the interactive architecture canvas: [netwatch-architecture.canvas.tsx](file:///C:/Users/ADMIN/.cursor/projects/c-Users-ADMIN-Desktop-tera-project-app/canvases/netwatch-architecture.canvas.tsx)

## Quick Start (Development)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python seed.py             # Creates admin/admin123 + sample devices
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — sign in with `admin` / `admin123`.

## GNS3 Deployment (Ubuntu Desktop VM)

### 1. GNS3 Topology Setup

```
[Cloud/NAT] ── [Ubuntu Desktop VM] ── [Management Switch] ── [R1, SW1, ...]
                     │
              NetWatch AI runs here
              NIC: 192.168.1.10 (example)
```

- Add an **Ubuntu Desktop** QEMU VM to your GNS3 project
- Connect its NIC to the same network as device management interfaces
- Ensure devices have reachable management IPs (e.g. 192.168.1.1, 192.168.1.2)

### 2. Install on Ubuntu VM

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nodejs npm iputils-ping

git clone <your-repo> /opt/netwatch
cd /opt/netwatch/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
GNS3_HOST=127.0.0.1          # GNS3 server on same machine
GNS3_PORT=3080
GNS3_PROJECT_ID=<your-project-uuid>
SECRET_KEY=<generate-random-key>
OPENAI_API_KEY=sk-...        # Or use Ollama locally
```

```bash
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

cd ../frontend && npm install && npm run build
# Serve with nginx or: npx serve dist -l 5173
```

### 3. GNS3 API Access

Enable the GNS3 REST API (default port 3080). The topology sync service:
- Polls `/v2/projects/{id}/nodes` every 60s
- Adds new nodes with management IPs
- Marks removed nodes as `removed` in the database

### 4. SSH Credentials

Set per-device SSH username/password in the Devices page or via API. For Cisco IOSv in GNS3, default is often `admin`/`admin` or `cisco`/`cisco`.

## Chatbot Examples

| User says | System does |
|-----------|-------------|
| "What's the network status?" | Polls all devices, returns up/down summary |
| "Any alerts?" | Lists active faults with recommendations |
| "Enable port 3 on switch1" | Creates pending config request for admin |
| "Generate network report" | Links to Reports page |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/signup` | Register |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/dashboard/stats` | KPI summary |
| GET | `/api/devices` | List devices |
| POST | `/api/devices/sync-topology` | Sync from GNS3 |
| POST | `/api/chat` | Send chatbot message |
| GET | `/api/reports/download/pdf` | Download PDF report |
| WS | `/ws/alerts` | Live alert stream |

## Roles

- **admin** — Approve SSH configs, sync topology, manage devices
- **operator** — Chat, view dashboard, request configs
- **viewer** — Read-only access

## Project Structure

```
app/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + WebSocket + background monitor
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── routers/          # API routes
│   │   └── services/         # Monitoring, SSH, AI, reports, topology
│   ├── requirements.txt
│   └── seed.py
└── frontend/
    └── src/
        ├── pages/            # Landing, Auth, Dashboard, Chat, Reports, Logs
        └── api.ts            # API client
```

## Security Notes

- Change default admin password immediately
- Store SSH passwords encrypted (set `FERNET_KEY` in production)
- Only admins can approve configuration changes
- All actions logged in audit trail
