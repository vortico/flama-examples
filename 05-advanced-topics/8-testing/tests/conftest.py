import collections
import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy
import src.app
from alembic import command
from alembic.config import Config as AlembicConfig
from filelock import FileLock
from flama.client import Client
from src import config


@pytest.fixture(scope="session")
def sqlalchemy_database(worker_id):
    database = (
        "test"
        if worker_id == "master"
        else f"test-{int(re.match(r'gw(\d+)', worker_id).group(1))}"  # pyright: ignore[reportOptionalMemberAccess]
    )

    engine = sqlalchemy.create_engine(
        config.DATABASE.url(
            config.APP.database, config.APP.database_user, config.APP.database_password
        ),
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as connection:
        connection.execute(sqlalchemy.text(f'DROP DATABASE IF EXISTS "{database}"'))
        connection.execute(sqlalchemy.text(f'CREATE DATABASE "{database}"'))

    yield collections.namedtuple("Database", ["test", "prod"])(
        test=database, prod=config.APP.database
    )

    with engine.connect() as connection:
        connection.execute(sqlalchemy.text(f'DROP DATABASE "{database}"'))


@pytest.fixture(scope="session", autouse=True)
def migrations(worker_id, sqlalchemy_database):
    alembic_cfg = AlembicConfig("alembic.ini")

    # Patch the APP config so Alembic's env.py reads the test database name dynamically
    with patch.object(config.APP, "database", sqlalchemy_database.test):
        if worker_id == "master":
            command.upgrade(alembic_cfg, "head")

            yield

            command.downgrade(alembic_cfg, "base")
        else:
            with FileLock(f"migration.lock.{worker_id}"):
                with FileLock("migration.lock"):
                    command.upgrade(alembic_cfg, "head")

            yield

            if not any(Path(".").glob("migration.lock.*")):
                with FileLock("migration.lock"):
                    command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="function")
async def app(sqlalchemy_database):
    _app = src.app.app

    # Switch SQLAlchemy connection to test database
    _app.sqlalchemy.database = config.DATABASE.url(
        sqlalchemy_database.test, config.APP.database_user, config.APP.database_password
    )

    return _app


@pytest.fixture(scope="function")
async def client(app):
    async with Client(app=app) as _client:
        yield _client


@pytest.fixture(scope="function", autouse=True)
async def connection(client):
    connection = await client.app.sqlalchemy.open_connection()
    transaction = await client.app.sqlalchemy.begin_transaction(connection)

    yield connection

    await client.app.sqlalchemy.end_transaction(transaction, rollback=True)
    await client.app.sqlalchemy.close_connection(connection)
