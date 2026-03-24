import asyncio
import pathlib

from flama import Flama, routing
from flama.client import Client

MODELS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "flama-site" / "public" / "models"
)


# ---------------------------------------------------------------------------
# Base application
# ---------------------------------------------------------------------------


class AppStatus:
    loaded = False


def home():
    """
    tags:
        - Home
    summary:
        Returns readiness message
    """
    return f"The API is ready. Loaded = {AppStatus.loaded}"


def user_me():
    """
    tags:
        - User
    summary:
        Returns hello 'John Doe'
    """
    username = "John Doe"
    return f"Hello {username}"


def user(username: str):
    """
    tags:
        - User
    summary:
        Returns hello 'username'
    """
    return f"Hello {username}"


async def startup():
    AppStatus.loaded = True


async def shutdown():
    AppStatus.loaded = False


app = Flama(
    openapi={
        "info": {
            "title": "Flama ML",
            "version": "0.1.0",
            "description": "Machine learning API using Flama 🔥",
        }
    },
    routes=[
        routing.Route("/", home),
        routing.Route("/user/me", user_me),
        routing.Route("/user/{username}", user),
    ],
    events={"startup": [startup], "shutdown": [shutdown]},
)

# ---------------------------------------------------------------------------
# Add models
# ---------------------------------------------------------------------------

app.models.add_model(
    path="/sklearn/",
    model=str(MODELS_DIR / "sklearn_model.flm"),
    name="sklearn-model",
)

app.models.add_model(
    path="/tensorflow/",
    model=str(MODELS_DIR / "tensorflow_model.flm"),
    name="tensorflow-model",
)

app.models.add_model(
    path="/pytorch/",
    model=str(MODELS_DIR / "pytorch_model.flm"),
    name="pytorch-model",
)

# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


async def main():
    async with Client(app=app) as client:
        r = await client.get("/")
        assert r.status_code == 200
        assert "True" in r.text
        print(f"1. GET /            => OK  {r.json()}")

        r = await client.get("/user/me")
        assert r.status_code == 200
        print(f"2. GET /user/me     => OK  {r.json()}")

        r = await client.get("/user/Alice")
        assert r.status_code == 200
        print(f"3. GET /user/Alice  => OK  {r.json()}")

        r = await client.get("/sklearn/")
        assert r.status_code == 200
        body = r.json()
        assert body["meta"]["framework"]["lib"] == "sklearn"
        print(
            f"4. GET /sklearn/    => OK  (framework={body['meta']['framework']['lib']})"
        )

        r = await client.post(
            "/sklearn/predict/", json={"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        )
        assert r.status_code == 200
        assert r.json()["output"] == [0, 1, 1, 0]
        print(f"5. POST /sklearn/predict/ => OK  output={r.json()['output']}")

        r = await client.get("/tensorflow/")
        assert r.status_code == 200
        body = r.json()
        assert body["meta"]["framework"]["lib"] == "tensorflow"
        print(
            f"6. GET /tensorflow/ => OK  (framework={body['meta']['framework']['lib']})"
        )

        r = await client.post(
            "/tensorflow/predict/", json={"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        )
        assert r.status_code == 200
        print(f"7. POST /tensorflow/predict/ => OK  output={r.json()['output']}")

        r = await client.get("/pytorch/")
        assert r.status_code == 200
        body = r.json()
        assert body["meta"]["framework"]["lib"] == "torch"
        print(
            f"8. GET /pytorch/    => OK  (framework={body['meta']['framework']['lib']})"
        )

        r = await client.post(
            "/pytorch/predict/", json={"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        )
        assert r.status_code == 200
        print(f"9. POST /pytorch/predict/ => OK  output={r.json()['output']}")

    print("\n=== 2-add-models: ALL PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
