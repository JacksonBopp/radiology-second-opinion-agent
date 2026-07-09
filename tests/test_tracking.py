import mlflow

from src.mlops.tracking import DEFAULT_EXPERIMENT_NAME, tracked_run


def test_tracked_run_logs_params_and_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path.as_posix()}/mlflow.db")

    with tracked_run("unit-test-run", params={"lr": 0.01}):
        mlflow.log_metric("auc", 0.9)

    runs = mlflow.search_runs(experiment_names=[DEFAULT_EXPERIMENT_NAME])

    assert not runs.empty
    assert runs.iloc[0]["params.lr"] == "0.01"
    assert runs.iloc[0]["metrics.auc"] == 0.9
