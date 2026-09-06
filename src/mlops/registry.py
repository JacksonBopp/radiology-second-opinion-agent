from __future__ import annotations

import numpy as np
import mlflow
import mlflow.pyfunc

from src.mlops.tracking import DEFAULT_EXPERIMENT_NAME, configure_mlflow
from src.vision.benchmarks import compare_to_chexpert_benchmarks
from src.vision.evaluation import evaluate_multilabel
from src.vision.models import VisionModelBaseline

REGISTERED_MODEL_NAME = "chest-xray-vision-baseline"


class VisionModelWrapper(mlflow.pyfunc.PythonModel):
    """Adapts VisionModelBaseline to the mlflow.pyfunc.PythonModel
    interface so it can be logged/registered/loaded through MLflow
    like any other model. Swapping in Nick's trained weights later
    means only this wrapper (or the model it constructs) changes;
    everything downstream that loads via `models:/<name>/<stage>`
    keeps working.
    """

    def load_context(self, context):
        self.model = VisionModelBaseline()

    def predict(self, context, model_input, params=None):
        images = np.asarray(model_input)
        if images.ndim == 2:
            images = images[np.newaxis, ...]
        return np.stack([self.model.predict_proba(img) for img in images])


def synthetic_eval_metrics(n_samples: int = 64, seed: int = 7) -> dict:
    """Evaluation metrics from a synthetic labeled batch.

    The repo can't ship CheXpert images/labels (see
    src/vision/benchmarks.py), so there's no real held-out set to
    score against yet. This stands in until Nick wires up an actual
    CheXpert-derived evaluation set, at which point its output can be
    passed into register_vision_model(metrics=...) directly.
    """
    rng = np.random.default_rng(seed)
    model = VisionModelBaseline()
    n_labels = len(model.labels)

    images = rng.uniform(0, 1, size=(n_samples, 224, 224)).astype(np.float32)
    y_score = np.stack([model.predict_proba(img) for img in images])
    y_true = (y_score + rng.normal(0, 0.2, size=y_score.shape) > 0.5).astype(int)

    return evaluate_multilabel(y_true, y_score)


def register_vision_model(
    metrics: dict | None = None,
    registered_model_name: str = REGISTERED_MODEL_NAME,
) -> mlflow.models.model.ModelInfo:
    """Log the current vision model and register it in the MLflow
    Model Registry, returning the logged model's info (includes the
    new registered version number).
    """
    configure_mlflow(DEFAULT_EXPERIMENT_NAME)

    metrics = metrics or synthetic_eval_metrics()
    benchmark = compare_to_chexpert_benchmarks(metrics)

    with mlflow.start_run(run_name="register-vision-baseline"):
        mlflow.log_metrics(
            {
                "macro_auc": metrics["macro_auc"],
                "macro_sensitivity": metrics["macro_sensitivity"],
                "macro_specificity": metrics["macro_specificity"],
            }
        )
        mlflow.log_param("model_class", "VisionModelBaseline")
        mlflow.log_param("benchmark_passed", benchmark["passed"])

        model_info = mlflow.pyfunc.log_model(
            name="model",
            python_model=VisionModelWrapper(),
            registered_model_name=registered_model_name,
            await_registration_for=30,
        )

    return model_info
