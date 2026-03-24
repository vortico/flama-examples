import asyncio
import pathlib
import typing as t
from datetime import datetime

import pydantic

from flama import Flama, types
from flama.client import Client
from flama.models import ModelResource
from flama.resources.routing import ResourceRoute

MODELS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "flama-site" / "public" / "models"
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = Flama(
    openapi={
        "info": {
            "title": "Flama ML",
            "version": "0.1.0",
            "description": "Machine learning API using Flama 🔥",
        }
    },
    docs="/docs/",
    schema="/schema/",
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class X(pydantic.BaseModel):
    input: list[t.Any]


class Y(pydantic.BaseModel):
    output: list[t.Any]


# ---------------------------------------------------------------------------
# Custom ModelResource
# ---------------------------------------------------------------------------


class MySKModel(ModelResource):
    verbose_name = "My ScikitLearn Model"
    model_path = str(MODELS_DIR / "sklearn_model.flm")
    name = "sk_model"

    @ResourceRoute.method("/predict/", methods=["POST"], name="model-predict")
    def predict(
        self, data: t.Annotated[types.Schema, types.SchemaMetadata(X)]
    ) -> t.Annotated[types.Schema, types.SchemaMetadata(Y)]:
        """
        tags:
            - My ScikitLearn Model
        summary:
            Run predict method.
        description:
            This is a more detailed description of the predict method.
        responses:
            200:
                description: ML model prediction.
        """
        return {"output": self.model.predict(data["input"])}

    @ResourceRoute.method("/inspect/", methods=["GET"], name="model-inspect-model")
    def inspect_model(self):
        """
        tags:
            - My ScikitLearn Model
        summary:
            Get metadata info.
        description:
            Returns the model inspection data.
        responses:
            200:
                description: ML model info.
        """
        return {"params": self.model.inspect()}

    info = {
        "model_version": "1.0.0",
        "library_version": "1.0.2",
    }

    @ResourceRoute.method("/metadata/", methods=["GET"], name="metadata-method")
    def metadata(self):
        """
        tags:
            - My ScikitLearn Model
        summary:
            Get metadata info.
        description:
            Returns metadata information about the model.
        responses:
            200:
                description: ML model metadata.
        """
        return {
            "metadata": {
                "built-in": {
                    "verbose_name": self._meta.verbose_name,
                    "name": self._meta.name,
                },
                "custom": {
                    **self.info,
                    "date": str(datetime.now().date()),
                    "time": str(datetime.now().time()),
                },
            }
        }


app.models.add_model_resource(path="/sklearn", resource=MySKModel)

# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


async def main():
    async with Client(app=app) as client:
        r = await client.post(
            "/sklearn/predict/", json={"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        )
        assert r.status_code == 200
        assert r.json()["output"] == [0, 1, 1, 0]
        print(f"1. POST /sklearn/predict/ => OK  output={r.json()['output']}")

        r = await client.get("/sklearn/inspect/")
        assert r.status_code == 200
        assert "params" in r.json()
        print("2. GET /sklearn/inspect/ => OK")

        r = await client.get("/sklearn/metadata/")
        assert r.status_code == 200
        body = r.json()
        assert body["metadata"]["built-in"]["verbose_name"] == "My ScikitLearn Model"
        print(
            f"3. GET /sklearn/metadata/ => OK  verbose_name={body['metadata']['built-in']['verbose_name']}"
        )

        r = await client.get("/sklearn/")
        assert r.status_code == 200
        print("4. GET /sklearn/ (default inspect) => OK")

    print("\n=== 3-model-resource: ALL PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
