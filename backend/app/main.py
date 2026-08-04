import asyncio
import json
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import async_session, init_db
from app.models import Alert
from app.routers import auth, dashboard, devices
from app.services.monitoring import poll_all_devices
from app.services.topology import sync_topology
from sqlalchemy import select, desc

settings = get_settings()


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.discard(ws)


manager = ConnectionManager()


async def background_monitor():
    """Poll devices and sync topology on interval."""
    while True:
        try:
            async with async_session() as db:
                await poll_all_devices(db)
                await sync_topology(db)
                await db.commit()

                result = await db.execute(
                    select(Alert).where(Alert.is_acknowledged == False).order_by(desc(Alert.created_at)).limit(5)
                )
                alerts = result.scalars().all()
                if alerts:
                    await manager.broadcast({
                        "type": "alerts",
                        "alerts": [
                            {
                                "id": a.id,
                                "severity": a.severity.value,
                                "title": a.title,
                                "message": a.message,
                                "recommendation": a.recommendation,
                            }
                            for a in alerts
                        ],
                    })
        except Exception as e:
            print(f"Monitor error: {e}")
        await asyncio.sleep(settings.poll_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(background_monitor())
    yield
    task.cancel()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
