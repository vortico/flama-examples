import asyncio
import uuid
import typing as t

from flama import Flama
from flama.client import Client
from flama.middleware import Middleware
from flama.authentication import (
    AccessTokenComponent,
    AuthenticationMiddleware,
    AccessToken,
)
from flama.authentication.jwt import jwt

SECRET_KEY = uuid.UUID(int=0).bytes

app = Flama(
    components=[AccessTokenComponent(secret=SECRET_KEY)],
    middleware=[Middleware(AuthenticationMiddleware)],
)


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@app.route("/public/", methods=["GET"])
async def public_info():
    return {"message": "This is public information."}


@app.route("/login/", methods=["POST"])
async def login():
    jwt_token = jwt.JWT(
        {"alg": "HS256", "typ": "JWT"},
        {
            "data": {
                "user_id": 123,
                "permissions": ["read:secure"],
            },
            "iat": 0,
        },
    )

    token_string = jwt_token.encode(SECRET_KEY).decode()

    return {"token": token_string}


# ---------------------------------------------------------------------------
# Protected endpoints
# ---------------------------------------------------------------------------


@app.route("/secure/", methods=["GET"], tags={"permissions": ["read:secure"]})
async def secure_info():
    return {"message": "You have accessed the secure vault!"}


@app.route("/me/", methods=["GET"], tags={"permissions": ["read:secure"]})
async def current_user(token: AccessToken):
    return {"your_token_data": token.to_dict()}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


async def main():
    async with Client(app=app) as client:
        # Step 1: Public route
        response = await client.get("/public/")
        print(f"Public:  {response.status_code}, {response.json()}")

        # Step 2: Protected route without token
        response = await client.get("/secure/")
        print(f"Secure (no token): {response.status_code}, {response.json()}")

        # Step 3: Login
        response = await client.post("/login/")
        token_string = response.json()["token"]
        print(f"Token:   {token_string[:20]}...")

        # Step 4: Protected route with token
        headers = {"access_token": f"Bearer {token_string}"}

        response = await client.get("/secure/", headers=headers)
        print(f"Secure (with token): {response.status_code}, {response.json()}")

        # Step 5: Token introspection
        response = await client.get("/me/", headers=headers)
        print(f"Me:      {response.status_code}, {response.json()}")


if __name__ == "__main__":
    asyncio.run(main())
