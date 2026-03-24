import typing as t
import uuid

import pydantic
import sqlalchemy
from flama.ddd.repositories.sqlalchemy import SQLAlchemyTableRepository
from flama.sqlalchemy import metadata

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
# Schemas
# ---------------------------------------------------------------------------


class UserCredentials(pydantic.BaseModel):
    email: str
    password: str


class UserDetails(UserCredentials):
    name: str
    surname: str


class User(UserDetails):
    id: t.Optional[str] = None
    active: t.Optional[bool] = False


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class UserRepository(SQLAlchemyTableRepository):
    _table = user_table


class ExtendedUserRepository(SQLAlchemyTableRepository):
    _table = user_table

    async def count_active_users(self) -> int:
        result = await self._connection.execute(
            self._table.select().where(self._table.c.active == True)  # noqa: E712
        )
        return len(result.all())


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    from sqlalchemy import create_engine
    from sqlalchemy.ext.asyncio import create_async_engine

    DATABASE_URL_SYNC = "sqlite:///ddd_repo_demo.db"
    DATABASE_URL_ASYNC = "sqlite+aiosqlite:///ddd_repo_demo.db"

    async def main():
        sync_engine = create_engine(DATABASE_URL_SYNC, echo=False)
        metadata.create_all(sync_engine)
        sync_engine.dispose()
        print("Database created.")

        engine = create_async_engine(DATABASE_URL_ASYNC)
        async with engine.connect() as connection:
            repo = UserRepository(connection)

            user_id = str(uuid.uuid4())
            created = await repo.create(
                {
                    "id": user_id,
                    "name": "Alice",
                    "surname": "Smith",
                    "email": "alice@example.com",
                    "password": "hashed_password",
                    "active": False,
                }
            )
            await connection.commit()
            print(f"Created: {created}")

            user = await repo.retrieve(id=user_id)
            print(f"Retrieved: {user}")

            updated = await repo.update({"active": True}, id=user_id)
            await connection.commit()
            print(f"Updated: {updated}")

            users = [u async for u in repo.list()]
            print(f"All users: {users}")

            await repo.delete(id=user_id)
            await connection.commit()
            print("User deleted.")

        await engine.dispose()
        print("Done.")

    asyncio.run(main())
