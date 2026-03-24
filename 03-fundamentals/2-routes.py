import datetime

import flama
from flama import Flama, websockets
from flama.http import HTMLResponse, JSONResponse
from flama.routing import Route, Router

app = Flama(
    openapi={
        "info": {
            "title": "Hello-🔥",
            "version": "1.0",
            "description": "My first API",
        },
    },
)


# ---------------------------------------------------------------------------
# Basic routes with decorators
# ---------------------------------------------------------------------------


@app.get("/")
async def root_path():
    return HTMLResponse(
        "<h1>Welcome to the <FlamaName /> Routes Example!</h1><p>Explore different endpoints.</p>"
    )


@app.get("/items/{item_id:int}/")
async def get_item_by_id(item_id: int):
    return JSONResponse(
        {
            "item_id": item_id,
            "description": f"Details for item ID: {item_id}",
            "parameter_type": str(type(item_id).__name__),
        }
    )


@app.post("/items/")
async def create_new_item():
    return JSONResponse(
        {"message": "Item created successfully (simulated)."}, status_code=201
    )


@app.get("/users/{username:str}/profile/")
async def get_user_profile(username: str):
    return {
        "username": username,
        "email": f"{username}@example.com",
        "status": "active",
    }


# ---------------------------------------------------------------------------
# Explicitly adding a route
# ---------------------------------------------------------------------------


async def system_status_handler():
    return {
        "status": "All systems operational",
        "server_time": datetime.datetime.now(),
    }


app.add_route(
    "/system/status/", system_status_handler, methods=["GET"], name="system_status"
)


# ---------------------------------------------------------------------------
# Not recommended: grouping routes with a Router
# ---------------------------------------------------------------------------


async def list_products():
    return [
        {"id": "prod_001", "name": "Awesome Gadget"},
        {"id": "prod_002", "name": "Super Tool"},
    ]


async def get_product_details(product: str):
    return {
        "sku": product,
        "name": f"Product {product.upper()}",
        "price": "99.99",
    }


product_router = Router(
    app=app,
    routes=[
        Route("/products/", list_products, methods=["GET"]),
        Route("/product_details/", get_product_details, methods=["GET"]),
    ],
)

app.mount("/router", product_router)


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@app.websocket_route("/ws-echo/")
async def websocket_echo_endpoint(websocket: websockets.WebSocket):
    try:
        await websocket.accept()
        await websocket.send_text("Hello from websocket. Following with echo...")
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo from Flama: {data}")
    except Exception as e:
        await websocket.close(1003)
        raise e from None
    else:
        await websocket.close()


# ---------------------------------------------------------------------------
# Recommended: grouping routes with sub-applications
# ---------------------------------------------------------------------------

shop_app = Flama()


@shop_app.get("/products/")
async def list_products_shop():
    return await list_products()


@shop_app.get("/product_details/")
async def get_product_details_shop(product: str):
    return await get_product_details(product)


app.mount("/api/v1/shop", product_router)


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
