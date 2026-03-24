import typing as t
import uuid

import pydantic

import flama
from flama import Flama, schemas

PUPPIES_DB_PYDANTIC: t.List[t.Dict[str, t.Any]] = []


class Puppy(pydantic.BaseModel):
    id: uuid.UUID
    name: str
    age: int

    @pydantic.field_validator("age")
    @classmethod
    def age_validation(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Age must be a non-negative number.")
        if v > 30:
            raise ValueError("Age seems too high for a puppy.")
        return v


class PuppyCreatePayload(pydantic.BaseModel):
    name: str
    age: int

    @pydantic.field_validator("age")
    @classmethod
    def age_validation(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Age must be a non-negative number.")
        if v > 30:
            raise ValueError("Age seems too high for a puppy.")
        return v


app = Flama(
    openapi={"info": {"title": "Puppy Register (Pydantic)", "version": "0.1.0"}},
    schema_library="pydantic",
)

app.schema.register_schema(name="Puppy", schema=Puppy)
app.schema.register_schema(name="PuppyCreationPayload", schema=PuppyCreatePayload)

PuppyListResponse = t.Annotated[list[schemas.Schema], schemas.SchemaMetadata(Puppy)]
PuppyDetailResponse = t.Annotated[schemas.Schema, schemas.SchemaMetadata(Puppy)]
PuppyCreateRequest = t.Annotated[
    schemas.Schema, schemas.SchemaMetadata(PuppyCreatePayload)
]


@app.get("/puppies/")
async def list_puppies_pydantic(name: t.Optional[str] = None) -> PuppyListResponse:
    return [p for p in PUPPIES_DB_PYDANTIC if name is None or p.get("name") == name]


@app.post("/puppies/")
async def create_puppy_pydantic(
    puppy_input_dict: PuppyCreateRequest,
) -> PuppyDetailResponse:
    puppy = {
        "name": puppy_input_dict["name"],
        "age": puppy_input_dict["age"],
        "id": uuid.uuid4(),
    }

    Puppy.model_validate(puppy)
    PUPPIES_DB_PYDANTIC.append(puppy)

    return puppy


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
