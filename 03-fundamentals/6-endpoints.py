import typing

import pydantic

import flama
from flama import Flama, http, schemas
from flama.endpoints import HTTPEndpoint

ITEMS_DB = {
    "item_001": {"name": "Awesome Gadget", "price": 99.99},
    "item_002": {"name": "Super Tool", "price": 49.50},
}


class Item(pydantic.BaseModel):
    name: str
    price: float


app = Flama()


# ---------------------------------------------------------------------------
# Function-based endpoints
# ---------------------------------------------------------------------------


@app.get("/{id:str}/")
async def get(id: str):
    if id not in ITEMS_DB:
        return http.JSONResponse({"error": "Item not found"}, status_code=404)
    return http.JSONResponse(ITEMS_DB[id])


@app.put("/{id:str}/")
async def put(
    item_id: str,
    item: typing.Annotated[schemas.Schema, schemas.SchemaMetadata(Item)],
):
    if item_id not in ITEMS_DB:
        return http.JSONResponse({"error": "Item not found"}, status_code=404)

    ITEMS_DB[item_id].update(item)
    return http.JSONResponse(ITEMS_DB[item_id])


# ---------------------------------------------------------------------------
# Class-based endpoint
# ---------------------------------------------------------------------------


@app.route("/items/")
class ItemEndpoint(HTTPEndpoint):
    async def get(self, id: str):
        if id not in ITEMS_DB:
            return http.JSONResponse({"error": "Item not found"}, status_code=404)
        return http.JSONResponse(ITEMS_DB[id])

    async def put(
        self,
        id: str,
        item: typing.Annotated[schemas.Schema, schemas.SchemaMetadata(Item)],
    ):
        if id not in ITEMS_DB:
            return http.JSONResponse({"error": "Item not found"}, status_code=404)

        ITEMS_DB[id].update(item)
        return http.JSONResponse(ITEMS_DB[id])


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
