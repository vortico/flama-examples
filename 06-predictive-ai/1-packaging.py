import datetime
import json
import pathlib
import tempfile
import uuid

import numpy as np

import flama
from sklearn.neural_network import MLPClassifier

# ---------------------------------------------------------------------------
# Train a simple model on the XOR dataset
# ---------------------------------------------------------------------------

X_train = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
Y_train = np.array([0, 1, 1, 0])

model = MLPClassifier(
    activation="tanh", max_iter=2000, hidden_layer_sizes=(10,), random_state=1
)
model.fit(X_train, Y_train)

# ---------------------------------------------------------------------------
# Dump with full metadata
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmpdir:
    output = pathlib.Path(tmpdir)

    artifact_path = output / "artifact.json"
    artifact_path.write_text(json.dumps({"description": "Sample artifact"}))

    flama.dump(
        model,
        path=output / "sklearn_model.flm",
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
        artifacts={"foo.json": str(artifact_path)},
    )

    art = flama.load(path=output / "sklearn_model.flm")
    assert art.model is not None
    assert art.meta.model.params == {"optimizer": "adams"}
    assert art.meta.model.metrics == {"recall": "0.95"}
    assert art.meta.extra["model_author"] == "John Doe"
    assert art.artifacts is not None and "foo.json" in art.artifacts
    preds = art.model.predict(X_train).tolist()
    print(f"[dump+load full metadata]  predictions={preds}  OK")

# ---------------------------------------------------------------------------
# Dump with minimal arguments (default compression = zstd)
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmpdir:
    flama.dump(model, path=pathlib.Path(tmpdir) / "minimal.flm", family="ml")
    art = flama.load(path=pathlib.Path(tmpdir) / "minimal.flm")
    assert art.model is not None
    print("[dump+load minimal]        OK")

# ---------------------------------------------------------------------------
# Compression formats
# ---------------------------------------------------------------------------

for fmt in ("bz2", "lzma", "zlib", "zstd"):
    with tempfile.TemporaryDirectory() as tmpdir:
        p = pathlib.Path(tmpdir) / f"model_{fmt}.flm"
        flama.dump(model, path=p, family="ml", compression=fmt)
        size = p.stat().st_size
        loaded = flama.load(path=p)
        assert loaded.model is not None
        print(f"[compression={fmt:4s}]          size={size:>7d} bytes  OK")

# ---------------------------------------------------------------------------
# TensorFlow dump / load
# ---------------------------------------------------------------------------

import tensorflow as tf

tf_model = tf.keras.models.Sequential(
    [
        tf.keras.layers.Flatten(input_shape=(2,)),
        tf.keras.layers.Dense(10, activation="tanh"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ]
)
tf_model.compile(optimizer="adam", loss="mse")
tf_model.fit(
    np.array([[0, 0], [0, 1], [1, 0], [1, 1]]),
    np.array([[0], [1], [1], [0]]),
    epochs=2000,
    verbose=0,
)

with tempfile.TemporaryDirectory() as tmpdir:
    flama.dump(tf_model, path=pathlib.Path(tmpdir) / "tensorflow_model.flm", family="ml")
    art = flama.load(path=pathlib.Path(tmpdir) / "tensorflow_model.flm")
    assert art.meta.framework.lib == "tensorflow"
    r = art.model.predict(np.array([[0, 0], [0, 1], [1, 0], [1, 1]]), verbose=0)
    preds = (r > 0.5).astype(int).flatten().tolist()
    print(f"[tensorflow dump+load]     predictions={preds}  OK")

# ---------------------------------------------------------------------------
# PyTorch dump / load
# ---------------------------------------------------------------------------

import torch


class XORModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.l1 = torch.nn.Linear(2, 10)
        self.l2 = torch.nn.Linear(10, 1)

    def forward(self, x):
        x = torch.tanh(self.l1(x))
        x = torch.sigmoid(self.l2(x))
        return x


X_pt = torch.Tensor([[0, 0], [0, 1], [1, 0], [1, 1]])
Y_pt = torch.Tensor([0, 1, 1, 0]).view(-1, 1)

pt_model = XORModel()
for m in pt_model.modules():
    if isinstance(m, torch.nn.Linear):
        m.weight.data.normal_(0, 1)

loss_fn = torch.nn.BCELoss()
optimizer = torch.optim.Adam(pt_model.parameters())
steps = X_pt.size(0)
for _ in range(2000):
    for _ in range(steps):
        dp = np.random.randint(steps)
        x_var = torch.autograd.Variable(X_pt[dp], requires_grad=False)
        y_var = torch.autograd.Variable(Y_pt[dp], requires_grad=False)
        optimizer.zero_grad()
        y_hat = pt_model(x_var)
        loss_result = loss_fn.forward(y_hat, y_var)
        loss_result.backward()
        optimizer.step()

with tempfile.TemporaryDirectory() as tmpdir:
    flama.dump(pt_model, path=pathlib.Path(tmpdir) / "pytorch_model.flm", family="ml")
    art = flama.load(path=pathlib.Path(tmpdir) / "pytorch_model.flm")
    assert art.meta.framework.lib == "torch"
    assert art.model is not None
    print("[pytorch dump+load]        OK")

print("\n=== 1-packaging: ALL PASSED ===")
