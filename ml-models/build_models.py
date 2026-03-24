import json
import pathlib
import tempfile
import uuid

import numpy as np

import flama

OUTPUT_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "flama-site" / "public" / "models"
)


def build_sklearn_model() -> None:
    from sklearn.neural_network import MLPClassifier

    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    Y = np.array([0, 1, 1, 0])

    for seed in range(100):
        model = MLPClassifier(
            activation="tanh",
            max_iter=2000,
            hidden_layer_sizes=(10,),
            random_state=seed,
        )
        model.fit(X, Y)
        if list(model.predict(X)) == [0, 1, 1, 0]:
            break
    else:
        raise RuntimeError("sklearn model failed to learn XOR after 100 seeds")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"description": "Example artifact for documentation"}, f)
        artifact_path = f.name

    flama.dump(
        model,
        path=OUTPUT_DIR / "sklearn_model.flm",
        model_id=uuid.UUID("cb659dec-ca09-40f8-a804-63c1f89113f6"),
        params={"solver": "adam"},
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

    pathlib.Path(artifact_path).unlink(missing_ok=True)
    print(f"  sklearn_model.flm  -> {OUTPUT_DIR / 'sklearn_model.flm'}")


def build_tensorflow_model() -> None:
    import tensorflow as tf

    model = tf.keras.models.Sequential(
        [
            tf.keras.layers.Flatten(input_shape=(2,)),
            tf.keras.layers.Dense(10, activation="tanh"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )

    model.compile(optimizer="adam", loss="mse")
    model.fit(
        np.array([[0, 0], [0, 1], [1, 0], [1, 1]]),
        np.array([[0], [1], [1], [0]]),
        epochs=2000,
        verbose=0,
    )

    flama.dump(model, path=OUTPUT_DIR / "tensorflow_model.flm")
    print(f"  tensorflow_model.flm -> {OUTPUT_DIR / 'tensorflow_model.flm'}")


def build_pytorch_model() -> None:
    import torch

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.l1 = torch.nn.Linear(2, 10)
            self.l2 = torch.nn.Linear(10, 1)

        def forward(self, x):
            x = torch.tanh(self.l1(x))
            x = torch.sigmoid(self.l2(x))
            return x

    X = torch.Tensor([[0, 0], [0, 1], [1, 0], [1, 1]])
    Y = torch.Tensor([0, 1, 1, 0]).view(-1, 1)

    model = Model()

    for m in model.modules():
        if isinstance(m, torch.nn.Linear):
            m.weight.data.normal_(0, 1)

    loss_fn = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters())

    steps = X.size(0)
    for _ in range(2000):
        for _ in range(steps):
            data_point = np.random.randint(steps)
            x_var = torch.autograd.Variable(X[data_point], requires_grad=False)
            y_var = torch.autograd.Variable(Y[data_point], requires_grad=False)

            optimizer.zero_grad()
            y_hat = model(x_var)
            loss_result = loss_fn.forward(y_hat, y_var)
            loss_result.backward()
            optimizer.step()

    flama.dump(model, path=OUTPUT_DIR / "pytorch_model.flm")
    print(f"  pytorch_model.flm   -> {OUTPUT_DIR / 'pytorch_model.flm'}")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building model files into: {OUTPUT_DIR}\n")

    print("1/3  Scikit-Learn MLPClassifier (XOR)")
    build_sklearn_model()

    print("2/3  TensorFlow Sequential (XOR)")
    build_tensorflow_model()

    print("3/3  PyTorch Module (XOR)")
    build_pytorch_model()

    print("\nDone.")
