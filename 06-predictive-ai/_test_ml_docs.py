import datetime
import json
import pathlib
import tempfile
import uuid

import numpy as np

MODELS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "flama-site" / "public" / "models"
)


def test_dump_load_api():
    import flama
    from sklearn.neural_network import MLPClassifier

    model = MLPClassifier(
        activation="tanh", max_iter=2000, hidden_layer_sizes=(10,), random_state=0
    )
    model.fit(
        np.array([[0, 0], [0, 1], [1, 0], [1, 1]]),
        np.array([0, 1, 1, 0]),
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"test": "artifact"}, f)
        artifact_path = f.name

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = pathlib.Path(tmpdir) / "test_model.flm"

        flama.dump(
            model,
            path=output_path,
            family="ml",
            model_id=uuid.uuid4(),
            timestamp=datetime.datetime(2023, 3, 10, 11, 30, 0),
            params={"optimizer": "adams"},
            metrics={"recall": "0.95"},
            extra={
                "model_version": "1.0.0",
                "model_description": "This is a test model",
                "model_author": "John Doe",
                "model_license": "MIT",
                "tags": ["test", "example"],
            },
            artifacts={"foo.json": artifact_path},
        )

        assert output_path.exists()

        model_artifact = flama.load(path=output_path)

        assert model_artifact.model is not None
        assert model_artifact.meta is not None
        assert model_artifact.meta.model.params == {"optimizer": "adams"}
        assert model_artifact.meta.model.metrics == {"recall": "0.95"}
        assert model_artifact.meta.extra["model_version"] == "1.0.0"
        assert model_artifact.artifacts is not None
        assert "foo.json" in model_artifact.artifacts

    pathlib.Path(artifact_path).unlink(missing_ok=True)
    print("  PASS: dump/load API")


def test_compression_values():
    import flama
    from sklearn.neural_network import MLPClassifier

    model = MLPClassifier(max_iter=100, random_state=0)
    model.fit(np.array([[0, 0], [1, 1]]), np.array([0, 1]))

    for compression in ("bz2", "lzma", "zlib", "zstd"):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / f"test_{compression}.flm"
            flama.dump(model, path=path, family="ml", compression=compression)
            loaded = flama.load(path=path)
            assert loaded.model is not None
    print("  PASS: all compression values (bz2, lzma, zlib, zstd)")


def test_sklearn_model_file():
    import flama

    artifact = flama.load(path=MODELS_DIR / "sklearn_model.flm")
    assert artifact.meta.framework.lib == "sklearn"
    predictions = artifact.model.predict(
        np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    ).tolist()
    assert predictions == [0, 1, 1, 0]
    assert artifact.meta.model.params == {"solver": "adam"}
    assert artifact.meta.model.metrics == {"recall": "0.95"}
    assert artifact.artifacts is not None and "foo.json" in artifact.artifacts
    print("  PASS: sklearn_model.flm")


def test_tensorflow_model_file():
    import flama

    artifact = flama.load(path=MODELS_DIR / "tensorflow_model.flm")
    assert artifact.meta.framework.lib == "tensorflow"
    result = artifact.model.predict(
        np.array([[0, 0], [0, 1], [1, 0], [1, 1]]), verbose=0
    )
    predictions = (result > 0.5).astype(int).flatten().tolist()
    assert predictions == [0, 1, 1, 0]
    print("  PASS: tensorflow_model.flm")


def test_pytorch_model_file():
    import flama

    artifact = flama.load(path=MODELS_DIR / "pytorch_model.flm")
    assert artifact.meta.framework.lib == "torch"
    assert artifact.model is not None
    print("  PASS: pytorch_model.flm")


def test_resource_route_method():
    from flama.resources.routing import ResourceRoute

    assert hasattr(ResourceRoute, "method")
    assert callable(ResourceRoute.method)
    print("  PASS: ResourceRoute.method exists")


def test_base_model_class():
    from flama.models import BaseModel, MLModel

    assert BaseModel is not None
    assert hasattr(BaseModel, "inspect")
    assert hasattr(MLModel, "predict")
    print("  PASS: BaseModel/MLModel classes exist with inspect/predict")


if __name__ == "__main__":
    print("Testing ML documentation accuracy...\n")

    test_dump_load_api()
    test_compression_values()
    test_sklearn_model_file()
    test_tensorflow_model_file()
    test_pytorch_model_file()
    test_resource_route_method()
    test_base_model_class()

    print("\nAll tests passed.")
