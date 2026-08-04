"""Create initial admin user and sample devices for GNS3 lab testing."""
import asyncio
from app.database import async_session, init_db
from app.auth import hash_password
from app.models import User, UserRole, Device


async def seed():
    await init_db()
    async with async_session() as db:
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.username == "admin"))
        if not existing.scalar_one_or_none():
            admin = User(
                email="admin@netwatch.local",
                username="admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print("Created admin user: admin / admin123")

        devices = [
            {"name": "router1", "hostname": "R1", "management_ip": "192.168.1.1", "device_type": "cisco_ios"},
            {"name": "switch1", "hostname": "SW1", "management_ip": "192.168.1.2", "device_type": "cisco_ios"},
        ]
        for d in devices:
            result = await db.execute(select(Device).where(Device.name == d["name"]))
            if not result.scalar_one_or_none():
                db.add(Device(**d, ssh_username="admin", ssh_password_enc="admin"))
                print(f"Added device: {d['name']}")

        await db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
