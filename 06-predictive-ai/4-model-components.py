import asyncio
import pathlib
from datetime import datetime

import flama
from flama import Flama
from flama.client import Client
from flama.models import MLModel, ModelComponent, BaseMLResource
from flama.resources.routing import ResourceRoute

MODELS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "flama-site" / "public" / "models"
)


# ---------------------------------------------------------------------------
# Custom ModelComponent (lazy loading)
# ---------------------------------------------------------------------------


class MyCustomModelComponent(ModelComponent):
    def __init__(self, model_path: str):
        model = MLModel(path=pathlib.Path(model_path))
        super().__init__(model)

    async def startup(self) -> None:
        # Skip auto-loading on startup to demonstrate lazy loading
        pass

    def reset(self):
        self._model._backend = None

    @property
    def loaded(self) -> bool:
        return self._model._backend is not None

    def resolve(self) -> MLModel:
        if not self.loaded:
            self.load()

        return self._model


component = MyCustomModelComponent(str(MODELS_DIR / "sklearn_model.flm"))


# ---------------------------------------------------------------------------
# Custom ModelResource
# ---------------------------------------------------------------------------


class MyCustomModelResource(BaseMLResource[MyCustomModelComponent]):
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
                    "loaded": self.component.loaded,
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
