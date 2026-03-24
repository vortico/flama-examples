import typing as t

import flama
import pydantic
import sqlalchemy
from flama import Flama, exceptions, types
from flama.resources import Resource
from flama.resources.crud import CRUDResource
from flama.resources.routing import ResourceRoute
from flama.sqlalchemy import SQLAlchemyModule
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///animals.db"

# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

metadata = sqlalchemy.MetaData()
animal_table = sqlalchemy.Table(
    "animal",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("species", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("age", sqlalchemy.Integer, nullable=False),
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class Animal(pydantic.BaseModel):
    id: t.Optional[int] = None
    name: str
    species: str
    age: int


class CalcInput(pydantic.BaseModel):
    a: float
    b: float


class CalcResult(pydantic.BaseModel):
    operation: str
    result: float


class PuppyCheck(pydantic.BaseModel):
    is_puppy: bool
    name: str


class SeniorCheck(pydantic.BaseModel):
    is_senior: bool
    name: str


# ---------------------------------------------------------------------------
# Resource (primitive)
# ---------------------------------------------------------------------------


class CalculatorResource(Resource):
    name = "calculator"
    verbose_name = "Calculator"

    @ResourceRoute.method("/add/", methods=["POST"], name="add")
    def add(
        self, data: t.Annotated[types.Schema, types.SchemaMetadata(CalcInput)]
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(CalcResult)]:
        """
        tags:
            - Calculator
        summary:
            Add two numbers
        description:
            Performs addition on the input data.
        """
        return {"operation": "add", "result": data["a"] + data["b"]}

    @ResourceRoute.method("/subtract/", methods=["POST"], name="subtract")
    def subtract(
        self, data: t.Annotated[types.Schema, types.SchemaMetadata(CalcInput)]
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(CalcResult)]:
        """
        tags:
            - Calculator
        summary:
            Subtract two numbers
        description:
            Performs subtraction (a - b).
        """
        return {"operation": "subtract", "result": data["a"] - data["b"]}

    @ResourceRoute.method("/multiply/", methods=["POST"], name="multiply")
    def multiply(
        self, data: t.Annotated[types.Schema, types.SchemaMetadata(CalcInput)]
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(CalcResult)]:
        """
        tags:
            - Calculator
        summary:
            Multiply two numbers
        description:
            Performs multiplication on the input data.
        """
        return {"operation": "multiply", "result": data["a"] * data["b"]}

    @ResourceRoute.method("/divide/", methods=["POST"], name="divide")
    def divide(
        self, data: t.Annotated[types.Schema, types.SchemaMetadata(CalcInput)]
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(CalcResult)]:
        """
        tags:
            - Calculator
        summary:
            Divide two numbers
        description:
            Performs division (a / b). Returns error if b is 0.
        """
        if data["b"] == 0:
            raise exceptions.HTTPException(
                status_code=400, detail="Division by zero is not allowed."
            )
        return {"operation": "divide", "result": data["a"] / data["b"]}


# ---------------------------------------------------------------------------
# CRUDResource
# ---------------------------------------------------------------------------


class AnimalResource(CRUDResource):
    name = "animal"
    verbose_name = "Animal"

    model = animal_table
    schema = Animal

    @ResourceRoute.method("/{id}/is_puppy/", methods=["GET"], name="is-puppy")
    async def is_puppy(
        self, id: int, scope: types.Scope
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(PuppyCheck)]:
        """
        tags:
            - Animal
        summary:
            Check is puppy
        description:
            Checks if animal is a puppy using the app's shared database connection.
        """
        query = sqlalchemy.select(animal_table).where(animal_table.c.id == id)

        async with scope["root_app"].sqlalchemy.engine.connect() as conn:
            result = await conn.execute(query)
            animal_record = result.first()

        if not animal_record:
            raise exceptions.HTTPException(status_code=404, detail="Animal not found")

        return {"is_puppy": (animal_record.age < 1), "name": animal_record.name}

    @ResourceRoute.method("/{id}/is_senior/", methods=["GET"], name="is-senior")
    async def is_senior(
        self, id: int
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(SeniorCheck)]:
        """
        tags:
            - Animal
        summary:
            Check is senior
        description:
            Checks if animal is a senior by creating a new, independent connection.
        """
        query = sqlalchemy.select(animal_table).where(animal_table.c.id == id)

        engine = create_async_engine(DATABASE_URL)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(query)
                animal_record = result.first()
        finally:
            await engine.dispose()

        if not animal_record:
            raise exceptions.HTTPException(status_code=404, detail="Animal not found")

        return {"is_senior": (animal_record.age > 10), "name": animal_record.name}


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = Flama(
    openapi={
        "info": {
            "title": "Animal API",
            "version": "1.0",
            "description": "Demonstrating the evolution from Resource to CRUDResource.",
        },
    },
    modules=[SQLAlchemyModule(DATABASE_URL)],
)

app.resources.add_resource("/calculator/", CalculatorResource)
app.resources.add_resource("/animal/", AnimalResource)


@app.on_event("startup")
async def create_db():
    async with app.sqlalchemy.engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


if __name__ == "__main__":
    flama.run(
        flama_app="resources:app",
        server_host="0.0.0.0",
        server_port=8000,
        server_reload=True,
    )
