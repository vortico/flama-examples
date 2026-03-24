import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from src.models import metadata
from src.migrations import config


if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(
        config.DATABASE.url(
            config.APP.database, config.APP.database_user, config.APP.database_password
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


asyncio.run(run_async_migrations())
