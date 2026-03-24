import asyncio
import typing as t

from flama import Flama
from flama.client import Client
import pydantic


class Product(pydantic.BaseModel):
    id: int
    name: str
    price: float


INVENTORY: t.List[Product] = [
    Product(id=i, name=f"Widget {i}", price=10.0 + i) for i in range(1, 101)
]

app = Flama(
    openapi={
        "info": {
            "title": "Product API",
            "version": "1.0",
            "description": "A paginated API for product inventory.",
        }
    }
)


# ---------------------------------------------------------------------------
# Page number
# ---------------------------------------------------------------------------


@app.route("/catalogue/", methods=["GET"], pagination="page_number")
def get_catalogue(**kwargs) -> t.List[Product]:
    """
    tags:
        - Products
    summary:
        Product Catalogue
    description:
        Browse products using page numbers.
    responses:
        200:
            description: A paginated list of products.
    """
    return INVENTORY


# ---------------------------------------------------------------------------
# Limit-offset
# ---------------------------------------------------------------------------


@app.route("/feed/", methods=["GET"], pagination="limit_offset")
def get_feed(**kwargs) -> t.List[Product]:
    """
    tags:
        - Products
    summary:
        Product Feed
    description:
        Sync products using limit and offset.
    responses:
        200:
            description: A paginated list of products.
    """
    return INVENTORY


async def main():
    async with Client(app=app) as client:
        # Step 1: Page number
        print("\nPage Number Strategy (Page 2)")

        response = await client.get("/catalogue/", params={"page": 2, "page_size": 5})
        data = response.json()

        print(f" Request URL: {response.url}")
        print(f" Meta Info:   {data['meta']}")
        print(f" Data Count:  {len(data['data'])}")
        print(f" First Item:  {data['data'][0]['name']}")

        # Step 2: Limit-offset
        print("\nLimit-Offset Strategy (Skip 90, Take 5)")

        response = await client.get("/feed/", params={"limit": 5, "offset": 90})
        data = response.json()

        print(f" Request URL: {response.url}")
        print(f" Meta Info:   {data['meta']}")
        print(f" Data Count:  {len(data['data'])}")
        print(f" First Item:  {data['data'][0]['name']}")


if __name__ == "__main__":
    asyncio.run(main())
