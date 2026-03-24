import asyncio
import typing as t
import uuid

import httpx
import pydantic
import sqlalchemy
from flama import Flama, types
from flama.client import Client
from flama.ddd import WorkerComponent
from flama.ddd.repositories.http import HTTPResourceRepository
from flama.ddd.repositories.sqlalchemy import SQLAlchemyTableRepository
from flama.ddd.workers.http import HTTPWorker
from flama.ddd.workers.sqlalchemy import SQLAlchemyWorker
from flama.sqlalchemy import SQLAlchemyModule, metadata

# ===========================================================================
# Backend: SQL-backed Flama app
# ===========================================================================

user_table = sqlalchemy.Table(
    "user",
    metadata,
    sqlalchemy.Column(
        "id",
        sqlalchemy.String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    ),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("surname", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=False, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("active", sqlalchemy.Boolean, nullable=False),
)


class User(pydantic.BaseModel):
    id: t.Optional[str] = None
    name: str
    surname: str
    email: str
    password: str
    active: bool = False


class UserSQLRepository(SQLAlchemyTableRepository):
    _table = user_table


class BackendWorker(SQLAlchemyWorker):
    user: UserSQLRepository


backend = Flama(
    modules=[SQLAlchemyModule("sqlite+aiosqlite:///")],
    components=[WorkerComponent(worker=BackendWorker())],
)


@backend.on_event("startup")
async def on_startup():
    async with backend.sqlalchemy.engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


@backend.post("/user/")
async def create_user(
    worker: BackendWorker,
    data: t.Annotated[types.Schema, types.SchemaMetadata(User)],
):
    async with worker:
        created = await worker.user.create(dict(data))
    return created[0]


@backend.get("/user/{user_id}/")
async def get_user(worker: BackendWorker, user_id: str):
    async with worker:
        return await worker.user.retrieve(id=user_id)


@backend.put("/user/{user_id}/")
async def update_user(
    worker: BackendWorker,
    user_id: str,
    data: t.Annotated[types.Schema, types.SchemaMetadata(User)],
):
    async with worker:
        updated = await worker.user.update(dict(data), id=user_id)
    return updated[0]


@backend.delete("/user/{user_id}/")
async def delete_user(worker: BackendWorker, user_id: str):
    async with worker:
        await worker.user.delete(id=user_id)


# ===========================================================================
# Gateway: HTTPWorker-based app consuming the backend
# ===========================================================================


class UserHTTPRepository(HTTPResourceRepository):
    _resource = "/user"


class GatewayWorker(HTTPWorker):
    user: UserHTTPRepository


gateway = Flama(
    openapi={
        "info": {
            "title": "Gateway API",
            "version": "1.0.0",
            "description": "A gateway that consumes a remote Flama API",
        },
    },
    docs="/docs/",
    components=[
        WorkerComponent(
            worker=GatewayWorker(
                url="http://localapp",
                transport=httpx.ASGITransport(app=backend),
            )
        )
    ],
)


@gateway.post("/demo/")
async def demo_http_worker(worker: GatewayWorker):
    user_id = str(uuid.uuid4())

    async with worker:
        created = await worker.user.create(
            {
                "id": user_id,
                "name": "Alice",
                "surname": "Smith",
                "email": f"alice-{user_id[:8]}@example.com",
                "password": "hashed_secret",
                "active": True,
            }
        )
        user = await worker.user.retrieve(user_id)

    return {"created_user": user}


# ===========================================================================
# Demo
# ===========================================================================


async def main():
    async with Client(app=backend):
        async with Client(app=gateway) as client:
            response = await client.post("/demo/")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")


if __name__ == "__main__":
    asyncio.run(main())
