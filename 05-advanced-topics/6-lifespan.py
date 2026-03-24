import asyncio
import typing as t
from flama import Flama
from flama.client import Client


class NotificationService:
    def __init__(self, name: str):
        self.name = name
        self.is_online = False

    async def connect(self):
        print(f"[{self.name}] 📡 Connecting to gateway...")
        await asyncio.sleep(1)
        self.is_online = True
        print(f"[{self.name}] ✅ Connected.")

    async def disconnect(self):
        print(f"[{self.name}] 🔌 Closing connection...")
        await asyncio.sleep(1)
        self.is_online = False
        print(f"[{self.name}] 💤 Disconnected.")


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

app_events = Flama()
service_events = NotificationService("Events App")


@app_events.on_event("startup")
async def startup_service():
    await service_events.connect()


@app_events.on_event("shutdown")
async def shutdown_service():
    await service_events.disconnect()


@app_events.route("/events", methods=["GET"])
async def status_events():
    return {"status": "online", "service_ready": service_events.is_online}


# ---------------------------------------------------------------------------
# Custom lifespan
# ---------------------------------------------------------------------------


class ServiceLifespan:
    def __init__(self, app: Flama | None):
        self.app = app

    async def __aenter__(self):
        if self.app:
            service = NotificationService("Context App")
            await service.connect()
            setattr(self.app, "service", service)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.app and hasattr(self.app, "notification_service"):
            await self.app.service.disconnect()


app_context = Flama(lifespan=ServiceLifespan)


@app_context.route("/context", methods=["GET"])
async def status_context():
    service = getattr(app_context, "service", None)
    is_ready = service.is_online if service else False
    return {"status": "online", "service_ready": is_ready}


async def main():
    print("Testing Event Handlers...")
    async with Client(app=app_events) as client:
        response = await client.get("/events")
        print(f"[Client] Response: {response.json()}")

    print("Testing Custom Lifespan...")
    async with Client(app=app_context) as client:
        response = await client.get("/context")
        print(f"[Client] Response: {response.json()}")


if __name__ == "__main__":
    asyncio.run(main())
