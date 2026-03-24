import typing as t
import uuid

import typesystem

import flama
from flama import Flama, schemas

PUPPIES_DB_TYPESYSTEM: t.List[t.Dict[str, t.Any]] = []

puppy_output_schema = typesystem.Schema(
    fields={
        "id": typesystem.String(title="ID"),
        "name": typesystem.String(title="Name", max_length=100),
        "age": typesystem.Integer(title="Age", minimum=0, maximum=30),
    }
)

puppy_create_schema = typesystem.Schema(
    fields={
        "name": typesystem.String(title="Name", max_length=100, allow_null=False),
        "age": typesystem.Integer(title="Age", minimum=0, maximum=30, allow_null=False),
    }
)

app = Flama(
    openapi={"info": {"title": "Puppy Register (Typesystem)", "version": "0.1.0"}},
    schema_library="typesystem",
)

app.schema.register_schema(name="Puppy", schema=puppy_output_schema)
app.schema.register_schema(name="PuppyCreationPayload", schema=puppy_create_schema)

PuppyListResponse = t.Annotated[
    list[schemas.Schema], schemas.SchemaMetadata(puppy_output_schema)
]
PuppyDetailResponse = t.Annotated[
    schemas.Schema, schemas.SchemaMetadata(puppy_output_schema)
]
PuppyCreateRequest = t.Annotated[
    schemas.Schema, schemas.SchemaMetadata(puppy_create_schema)
]


@app.get("/puppies/")
async def list_puppies_typesystem(name: t.Optional[str] = None) -> PuppyListResponse:
    return [p for p in PUPPIES_DB_TYPESYSTEM if name is None or p.get("name") == name]


@app.post("/puppies/")
async def create_puppy_typesystem(
    puppy_input_dict: PuppyCreateRequest,
) -> PuppyDetailResponse:
    puppy = {
        "name": puppy_input_dict["name"],
        "age": puppy_input_dict["age"],
        "id": str(uuid.uuid4()),
    }

    puppy_output_schema.validate(puppy)
    PUPPIES_DB_TYPESYSTEM.append(puppy)

    return puppy


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
