import asyncio
import typing as t

import pydantic
import sqlalchemy
from flama import Flama
from flama.client import Client
from flama.resources.crud import CRUDResource
from flama.sqlalchemy import SQLAlchemyModule

metadata = sqlalchemy.MetaData()
table = sqlalchemy.Table(
    "animal",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
)


class Animal(pydantic.BaseModel):
    id: t.Optional[int] = None
    name: str


class AnimalResource(CRUDResource):
    name = "animal"
    model = table
    schema = Animal


app = Flama(
    modules=[SQLAlchemyModule("sqlite+aiosqlite:///")],
)
app.resources.add_resource("/animal/", AnimalResource)


@app.on_event("startup")
async def startup():
    async with app.sqlalchemy.engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def main():
    async with Client(app=app) as client:
        url_create = app.resolve_url("animal:create")
        print(f"\n[POST] Resolving 'animal:create' -> {url_create}")

        response = await client.post(str(url_create), json={"name": "Canna"})
        print(f"       Response: {response.json()}")

        url_list = app.resolve_url("animal:list")
        print(f"\n[GET]  Resolving 'animal:list'   -> {url_list}")

        response = await client.get(str(url_list))
        print(f"       Response: {response.json()}")

        url_retrieve = app.resolve_url("animal:retrieve", resource_id=1).path
        print(f"\n[GET]  Resolving 'animal:retrieve' (id=1) -> {url_retrieve}")

        response = await client.get(str(url_retrieve))
        print(f"       Response: {response.json()}")


if __name__ == "__main__":
    asyncio.run(main())
