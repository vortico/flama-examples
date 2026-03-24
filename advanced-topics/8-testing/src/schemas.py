import typing as t

import pydantic
from flama.resources.crud import CRUDResource

from src.models import table


class Animal(pydantic.BaseModel):
    id: t.Optional[int] = None
    name: str


class AnimalResource(CRUDResource):
    name = "animal"
    model = table
    schema = Animal
