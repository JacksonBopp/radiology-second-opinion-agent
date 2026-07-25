# Data & MLOps Report: Jackson Bopp

This covers everything I've built on the radiology-second-opinion-agent repo so far, as Data & MLOps Engineer, plus the parts of the Full Stack/Integration role I picked up to help Amrit out. Repo is here: https://github.com/JacksonBopp/radiology-second-opinion-agent

## Getting the project started

Set up the GitHub repo, wrote the initial README (team, roles, project description, related work, datasets), and added the rest of the team as collaborators.

## DICOM ingestion pipeline

Everything lives in `src/ingestion/`. The loader reads a DICOM file with pydicom and applies the modality LUT, so pixel values come out as real-world units (Hounsfield units for CT, for example) instead of raw stored integers. The preprocessing step handles windowing, normalization, resizing, and converting to uint8, basically getting an image ready for a CV model. The metadata module pulls the useful tags like modality, body part, and dimensions, and deliberately leaves out PatientName and PatientID so no PHI flows further into the system. All of this gets tied together in `pipeline.py`, which both the API and the async worker call.

Tests use the sample DICOM files that ship with pydicom, so nobody needs real patient scans to run the suite.

## MLOps and serving

Built the MLflow tracking helper (`src/mlops/tracking.py`) so experiments can be logged with a simple `tracked_run()` context manager. It uses a local sqlite backend by default and picks up `MLFLOW_TRACKING_URI` if you want to point it at a real server instead.

Set up the FastAPI app with a `/health` check and a `/scans` endpoint that takes an uploaded scan and runs it through the ingestion pipeline. Also wired up a Celery task that does the same processing asynchronously through Redis, matching what we sketched out in IDEA.md.

## Containers and CI

Wrote the Dockerfile and docker-compose setup connecting the api, worker, redis, and mlflow services, plus matching Kubernetes manifests. Set up GitHub Actions so the full test suite runs on every push and PR to master.

## Auth, audit logging, and feedback

This is the part I did to help Amrit, since he was covering two roles. Added API key authentication so requests need a valid key, a SQLite-backed audit log that records every request (method, path, status, who made it), and a feedback endpoint so a radiologist can submit corrections against a scan's findings. Both `/scans` and `/feedback` require auth now.

## Keeping things working as the team's code landed

Once Bryan's report generation layer, Nick's vision pipeline, and Amrit's agent orchestration all merged into master, I pulled everything in and checked it didn't break my side of things. It didn't, all 27 of my original tests kept passing. Found and fixed one real bug in the process: `tests/test_agents.py` was asserting the orchestrator returns `status: "success"`, but the orchestrator actually returns `"completed"` consistently everywhere else in its own code. Fixed the test to match, which got CI back to green. Also caught a stray `data/chromadb/` folder that the retrieval agent's tests create locally and made sure it's gitignored so nobody accidentally commits a binary vector database.

## Latest round: registry, drift monitoring, and deployment configs

The team gave me four more things to knock out:

**MLflow model registry.** Nick's vision model right now is a deterministic baseline, not a trained neural net yet, since there's no CheXpert data mounted to train against. I registered it anyway under the name `chest-xray-vision-baseline` so the registry workflow is proven out and ready. When real trained weights exist, they slot into the same flow without any code changes downstream.

**Drift monitoring, actually turned on.** Before this it was a module that worked in tests but wasn't hooked up to anything real. Now every scan that comes through `/scans` gets its features (pixel stats, dimensions, model confidence) logged to a small SQLite store, and there's a new `GET /monitoring/drift` endpoint that compares older scans against newer ones and returns a real drift report once enough data has come in.

**Docker with the frontend included.** Wrote a Dockerfile for the frontend that builds it with Node and serves it through nginx, with nginx set up to proxy API calls the same way the Vite dev server does. Added it to docker-compose as its own service. One thing worth being upfront about: Docker isn't installed on this machine. I checked pretty thoroughly (PATH, the usual install locations, WSL) and it's just not there. So these configs are written and the YAML is valid, but nobody has actually run a build with them yet. That still needs to happen on a machine that has Docker.

**Kubernetes manifests.** Added a deployment for the frontend and updated the API deployment to mount a persistent volume for the sqlite stores. While doing that I caught a real problem: the API deployment was set to run 2 replicas, but with a single shared volume and sqlite as the backing store, that setup would break the moment two pods tried to write at once. Dropped it to 1 replica and left a comment explaining why, so whoever picks this up next knows it needs a real database before it can scale. Same as Docker, there's no cluster available here to actually deploy and test against, so this is prepared but unverified.

## What's still open

- Somebody with Docker needs to actually build and run the containers, especially the frontend one, to confirm everything talks to each other correctly.
- Same thing for Kubernetes, once there's a cluster to deploy to.
- The sqlite-backed stores (audit log, feedback, drift features) work fine for now but will need to move to a real database before the API can run more than one replica.
- MLflow and drift monitoring are both live and logging, but they're only as useful as the model behind them. Once Nick has real trained weights, registering an updated model version and letting the drift monitor track it in production is basically the next natural step.

## Commit history

- `4aac708`: Initial commit, README and team info
- `62545d2`: DICOM ingestion and preprocessing pipeline
- `7306f15`: MLflow tracking, FastAPI serving, drift monitoring module, Docker/K8s, CI
- `eb6a08a`: API auth, audit logging, feedback capture
- `88a98bf`: Fixed the test_agents.py status mismatch that was breaking CI
- `2fd3611`: Gitignored the local ChromaDB folder
- `177f95f`: MLflow model registry and live drift monitoring
- `5aa2f1a`: Frontend added to Docker and Kubernetes configs
