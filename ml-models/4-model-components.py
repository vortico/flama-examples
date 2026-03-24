import asyncio
import pathlib
import typing
from datetime import datetime

import flama
from flama import Flama
from flama.client import Client
from flama.models import BaseModel, BaseModelResource, ModelComponent
from flama.resources.routing import ResourceRoute

MODELS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "flama-site" / "public" / "models"
)


# ---------------------------------------------------------------------------
# Custom Model
# ---------------------------------------------------------------------------


class MyCustomModel(BaseModel):
    def __init__(self, model=None, meta=None, artifacts=None):
        self.model = model
        self.meta = meta
        self.artifacts = artifacts

    def inspect(self) -> typing.Any:
        return self.model.get_params()

    def predict(self, x: typing.Any) -> typing.Any:
        result = self.model.predict(x)
        # numpy types are not JSON-serialisable
        return [int(v) for v in result] if hasattr(result, "tolist") else result


# ---------------------------------------------------------------------------
# Custom ModelComponent (lazy loading)
# ---------------------------------------------------------------------------


class MyCustomModelComponent(ModelComponent):
    def __init__(self, model_path: str):
        self._model_path = model_path
        self.model = MyCustomModel()

    def load(self):
        load_model = flama.load(path=self._model_path)
        self.model = MyCustomModel(
            load_model.model, load_model.meta, load_model.artifacts
        )

    def reset(self):
        self.model = MyCustomModel()

    def resolve(self) -> MyCustomModel:
        if not self.model.model:
            self.load()

        assert self.model.model
        return self.model


component = MyCustomModelComponent(str(MODELS_DIR / "sklearn_model.flm"))


# ---------------------------------------------------------------------------
# Custom ModelResource
# ---------------------------------------------------------------------------


class MyCustomModelResource(BaseModelResource[MyCustomModelComponent]):
    name = "custom_model"
    verbose_name = "Lazy-loaded ScikitLearn Model"
    component = component

    info = {
        "model_version": "1.0.0",
        "library_version": "1.0.2",
    }

    def _get_metadata(self):
        return {
            "metadata": {
                "built-in": {
                    "verbose_name": self._meta.verbose_name,
                    "name": self._meta.name,
                },
                "custom": {
                    **self.info,
                    "loaded": self.component.model.model is not None,
                    "date": str(datetime.now().date()),
                    "time": str(datetime.now().time()),
                },
            }
        }

    @ResourceRoute.method("/unload/", methods=["GET"], name="unload-method")
    def unload(self):
        """
        tags:
            - Lazy-loaded ScikitLearn Model
        summary:
            Unload the model.
        """
        self.component.reset()
        return self._get_metadata()

    @ResourceRoute.method("/metadata/", methods=["GET"], name="metadata-method")
    def metadata(self):
        """
        tags:
            - Lazy-loaded ScikitLearn Model
        summary:
            Get metadata info.
        """
        return self._get_metadata()


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
    components=[component],
)

app.models.add_model_resource(path="/model", resource=MyCustomModelResource)

# ---------------------------------------------------------------------------
# Integration test: lazy loading lifecycle
# ---------------------------------------------------------------------------


async def main():
    async with Client(app=app) as client:
        # Step 1: metadata before any model access — loaded=false
        r = await client.get("/model/metadata/")
        assert r.status_code == 200
        assert r.json()["metadata"]["custom"]["loaded"] is False
        print("1. GET /model/metadata/ => loaded=False  OK")

        # Step 2: inspect triggers lazy loading
        r = await client.get("/model/")
        assert r.status_code == 200
        print("2. GET /model/ (inspect) => OK  (lazy load triggered)")

        # Step 3: metadata after inspect — loaded=true
        r = await client.get("/model/metadata/")
        assert r.status_code == 200
        assert r.json()["metadata"]["custom"]["loaded"] is True
        print("3. GET /model/metadata/ => loaded=True  OK")

        # Step 4: predict
        r = await client.post(
            "/model/predict/", json={"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        )
        assert r.status_code == 200
        assert r.json()["output"] == [0, 1, 1, 0]
        print(f"4. POST /model/predict/ => output={r.json()['output']}  OK")

        # Step 5: unload resets the model
        r = await client.get("/model/unload/")
        assert r.status_code == 200
        assert r.json()["metadata"]["custom"]["loaded"] is False
        print("5. GET /model/unload/ => loaded=False  OK")

        # Step 6: predict after unload — triggers lazy load again
        r = await client.post(
            "/model/predict/", json={"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        )
        assert r.status_code == 200
        assert r.json()["output"] == [0, 1, 1, 0]
        print(f"6. POST /model/predict/ (reload) => output={r.json()['output']}  OK")

    print("\n=== 4-model-components: ALL PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
