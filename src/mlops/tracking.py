import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import mlflow

# MLflow's legacy filesystem tracking store is in maintenance mode as
# of mlflow 3.x, so the local fallback (used when MLFLOW_TRACKING_URI
# isn't set) is a sqlite db instead of a bare `mlruns/` directory.
# Point MLFLOW_TRACKING_URI at a real server (e.g. the docker-compose
# mlflow service) in other environments.
DEFAULT_TRACKING_DB = Path(__file__).resolve().parent.parent.parent / "mlruns.db"
DEFAULT_EXPERIMENT_NAME = "radiology-second-opinion"


def configure_mlflow(experiment_name: str = DEFAULT_EXPERIMENT_NAME) -> None:
    default_uri = f"sqlite:///{DEFAULT_TRACKING_DB.as_posix()}"
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", default_uri)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)


@contextmanager
def tracked_run(
    run_name: str,
    params: dict | None = None,
    tags: dict | None = None,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
) -> Iterator[None]:
    """Context manager wrapping an MLflow run: configures the tracking
    URI/experiment, logs the given params up front, then yields so the
    caller can log metrics/artifacts as training progresses.

    Usage:
        with tracked_run("vit-baseline", params={"lr": 1e-4}):
            mlflow.log_metric("val_auc", auc)
            mlflow.pytorch.log_model(model, "model")
    """
    configure_mlflow(experiment_name)
    with mlflow.start_run(run_name=run_name, tags=tags):
        if params:
            mlflow.log_params(params)
        yield
