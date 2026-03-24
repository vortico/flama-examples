import typing as t
import uuid

import flama
import pydantic
import sqlalchemy
from flama import Flama
from flama.ddd import WorkerComponent
from flama.ddd.repositories.sqlalchemy import SQLAlchemyTableRepository
from flama.ddd.workers.sqlalchemy import SQLAlchemyWorker
from flama.sqlalchemy import SQLAlchemyModule, metadata

# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class UserRepository(SQLAlchemyTableRepository):
    _table = user_table


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class RegisterWorker(SQLAlchemyWorker):
    user: UserRepository


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite+aiosqlite:///ddd_worker_demo.db"

app = Flama(
    openapi={
        "info": {
            "title": "Worker Demo API",
            "version": "1.0.0",
            "description": "Demonstrating the Worker (Unit of Work) pattern with Flama 🔥",
        },
    },
    docs="/docs/",
    modules=[SQLAlchemyModule(DATABASE_URL)],
    components=[WorkerComponent(worker=RegisterWorker())],
)


@app.on_event("startup")
async def on_startup():
    async with app.sqlalchemy.engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


@app.post("/demo/")
async def demo_worker(worker: RegisterWorker):
    """
    tags:
        - Demo
    summary:
        Worker demo
    description:
        Creates a user and retrieves it within an atomic unit of work.
    responses:
        200:
            description:
                Demonstration result with the created user.
    """
    user_id = str(uuid.uuid4())

    async with worker:
        await worker.user.create(
            {
                "id": user_id,
                "name": "Alice",
                "surname": "Smith",
                "email": f"alice-{user_id[:8]}@example.com",
                "password": "hashed_secret",
                "active": True,
            }
        )
        user = await worker.user.retrieve(id=user_id)

    return {"created_user": user}


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
