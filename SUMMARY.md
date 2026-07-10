# Summary of Changes — Jackson Bopp (Data & MLOps Engineer)

Covers work on the `radiology-second-opinion-agent` repo across four commits, plus the Full Stack/Integration pieces done in support of Amrit. All code is tested (27 passing tests) and verified against GitHub Actions CI.

## 1. Project setup

- Created the GitHub repo, README (team, roles, project description, related work, datasets), and added all four teammates as collaborators.

## 2. DICOM ingestion pipeline (`src/ingestion/`)

- `dicom_loader.py`: reads a DICOM file with pydicom and applies the modality LUT (e.g. converts stored CT values to Hounsfield units).
- `preprocess.py`: windowing/clipping, min-max normalization, resize, uint8 conversion — the steps needed before pixels reach a CV model.
- `metadata.py`: pulls non-identifying tags (modality, body part, dimensions, UIDs) and explicitly excludes PatientName/PatientID so PHI doesn't flow downstream.
- `pipeline.py`: ties the above together into one `process_scan_bytes()` function shared by the API and the async worker.
- Tests use pydicom's bundled sample DICOM files, so no real patient data is needed to run the suite.

## 3. MLOps / serving layer

- `src/mlops/tracking.py`: MLflow experiment tracking helper (`tracked_run()` context manager). Defaults to a local sqlite backend; set `MLFLOW_TRACKING_URI` to point at a real server.
- `src/api/main.py`: FastAPI app exposing `/health` and `POST /scans` (upload a scan, get back metadata + preprocessing stats).
- `src/worker/tasks.py`: Celery task wrapping the same pipeline for async processing via Redis, matching the architecture in IDEA.md.
- `src/monitoring/drift.py`: Evidently-based data drift reports over scan-level feature batches, for catching distribution shift once the system is in production.

## 4. Containerization & CI/CD

- `Dockerfile` + `docker-compose.yml`: wires together `api`, `worker`, `redis`, and `mlflow` services.
- `k8s/`: Deployment/Service manifests for the same four services (not yet cluster-tested — Docker isn't installed on this machine, so configs are YAML-validated but not build-tested).
- `.github/workflows/ci.yml`: runs the full test suite on every push/PR to `master`. Confirmed green on GitHub's runners.

## 5. Auth, audit logging, and feedback (helping Amrit — Full Stack/Integration role)

- `src/api/auth.py`: API key authentication (`X-API-Key` header), keys configured via `API_KEYS` env var as `name:key` pairs.
- `src/api/audit.py`: SQLite-backed audit trail middleware — logs every request's method, path, status code, and authenticated actor. Flagged explicitly in the team's architecture doc as required for a medical system.
- `src/api/feedback.py` + `/feedback` endpoints: lets a radiologist submit corrections against a scan's original model findings, stored and retrievable by `scan_id`. This is the "radiologist correction capture" piece from Amrit's role.
- `/scans` and `/feedback` now require a valid API key; `/health` stays open for uptime checks.

## What's still open on this role

- Docker/Kubernetes configs haven't been build/deploy-tested (no Docker on this machine).
- The React web UI, DICOM viewer with GradCAM overlay, and evaluation dashboard are still unbuilt — those are Amrit's remaining Full Stack/Integration items and depend partly on Nick's CV model existing first.
- MLflow tracking and the drift monitoring module are ready but have nothing to log yet until the ML Vision Engineer's model produces real predictions.

## Commit history

| Commit | Summary |
|---|---|
| `4aac708` | Initial commit: README, team info, IDEA.md |
| `62545d2` | DICOM ingestion and preprocessing pipeline |
| `7306f15` | MLflow tracking, FastAPI serving, drift monitoring, Docker/K8s, CI |
| `eb6a08a` | API auth, audit logging, feedback capture |

Repo: https://github.com/JacksonBopp/radiology-second-opinion-agent
