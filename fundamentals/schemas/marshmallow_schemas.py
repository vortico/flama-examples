import typing as t
import uuid

import marshmallow
from marshmallow import fields, validate

import flama
from flama import Flama, schemas

PUPPIES_DB_MARSHMALLOW: list[dict[str, t.Any]] = []


class PuppyOutput(marshmallow.Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    age = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=30, error="Age must be between 0 and 30."),
    )

    class Meta:
        ordered = True


class PuppyCreatePayload(marshmallow.Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    age = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=30, error="Age must be between 0 and 30."),
    )

    class Meta:
        ordered = True


app = Flama(
    openapi={"info": {"title": "Puppy Register (Marshmallow)", "version": "0.1.0"}},
    schema_library="marshmallow",
)

app.schema.register_schema(name="PuppyMM", schema=PuppyOutput)
app.schema.register_schema(name="PuppyCreationPayloadMM", schema=PuppyCreatePayload)

PuppyListResponse = t.Annotated[
    list[schemas.Schema], schemas.SchemaMetadata(PuppyOutput)
]
PuppyDetailResponse = t.Annotated[schemas.Schema, schemas.SchemaMetadata(PuppyOutput)]
PuppyCreateRequest = t.Annotated[
    schemas.Schema, schemas.SchemaMetadata(PuppyCreatePayload)
]


@app.get("/puppies/")
async def list_puppies_marshmallow(name: t.Optional[str] = None) -> PuppyListResponse:
    return [p for p in PUPPIES_DB_MARSHMALLOW if name is None or p.get("name") == name]


@app.post("/puppies/")
async def create_puppy_marshmallow(
    puppy_input: PuppyCreateRequest,
) -> PuppyDetailResponse:
    puppy = {
        "name": puppy_input["name"],
        "age": puppy_input["age"],
        "id": uuid.uuid4(),
    }

    PuppyOutput().validate(puppy)
    PUPPIES_DB_MARSHMALLOW.append(puppy)

    return puppy


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
