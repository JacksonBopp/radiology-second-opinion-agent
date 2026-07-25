import numpy as np
from mlflow.tracking import MlflowClient

from src.mlops.registry import REGISTERED_MODEL_NAME, register_vision_model, synthetic_eval_metrics


def test_synthetic_eval_metrics_shape():
    metrics = synthetic_eval_metrics(n_samples=8)

    assert "macro_auc" in metrics
    assert "macro_sensitivity" in metrics
    assert "macro_specificity" in metrics
    assert len(metrics["per_label"]) == 14


def test_register_vision_model_creates_new_version(tmp_path, monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path.as_posix()}/mlflow.db")

    model_info = register_vision_model(metrics=synthetic_eval_metrics(n_samples=8))

    assert model_info.registered_model_version is not None

    client = MlflowClient()
    versions = client.search_model_versions(f"name='{REGISTERED_MODEL_NAME}'")
    assert len(versions) >= 1


def test_register_vision_model_loads_and_predicts(tmp_path, monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path.as_posix()}/mlflow.db")
    import mlflow.pyfunc

    model_info = register_vision_model(metrics=synthetic_eval_metrics(n_samples=8))
    loaded = mlflow.pyfunc.load_model(model_info.model_uri)

    image = np.random.default_rng(1).uniform(0, 1, size=(224, 224)).astype(np.float32)
    prediction = loaded.predict(image[np.newaxis, ...])

    assert prediction.shape == (1, 14)
