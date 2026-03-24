import typing as t
import uuid

import pydantic
import sqlalchemy
from flama.sqlalchemy import metadata
from sqlalchemy import create_engine

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
# Migration
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///ddd_users.db"


def run_migration():
    engine = create_engine(DATABASE_URL, echo=False)
    metadata.create_all(engine)
    print("Database and User table created successfully.")


if __name__ == "__main__":
    run_migration()
