# Radiology Second-Opinion Agent

**Team:** The Nguyeners

## Team Members & Roles

| Member | Role |
|---|---|
| Jackson Bopp | Data & MLOps Engineer: data pipeline, model serving, infrastructure |
| Bryan Nguyen | GenAI & NLP Engineer: report generation, clinical language layer |
| Nicholas Toptchi | ML Vision Engineer: computer vision pipeline |
| Amrit Ganesh | Agentic Systems Engineer & Full Stack/Integration Engineer: orchestration/reasoning layer, UI/API integration |

See [IDEA.md](IDEA.md) for the detailed breakdown of responsibilities, architecture, and tech stack for each role.

## Project Description

A hackathon project: a system that analyzes chest X-rays, flags possible abnormalities, and writes a structured report like the one a radiologist would produce.

It works in three stages: a computer vision model checks the scan for findings such as pneumonia and lung nodules, an agent compares those findings with similar past cases and medical literature, and an LLM writes a report with ranked possible diagnoses and a confidence level for each.

It's meant as a second opinion, not a replacement for a radiologist, especially where specialists are hard to reach.

## Quickstart & Setup

### Prerequisites
- Docker & Docker Compose (for backend)
- Node.js & npm (for frontend)
- Python 3.10+ (for local development)

### 1. Environment Variables
Create a `.env` file in the root directory and add the following keys:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
*(Optional)* Add `CHROMA_DB_DIR=./chroma_db` if running locally without Docker.

### 2. Run the Backend (Docker)
The easiest way to run the API, MLflow, and Chroma vector store is via Docker Compose:
```bash
docker-compose up --build
```
- API will run on `http://localhost:8000`
- MLflow will run on `http://localhost:5000`
- API docs available at `http://localhost:8000/docs`

### 3. Run the Frontend (Vite + React)
In a separate terminal, install dependencies and start the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```
The web dashboard will be available at `http://localhost:5173`.

## Testing

### Python Backend Tests
Ensure your virtual environment is active and dependencies are installed, then run the test suite:
```bash
pytest tests/ -v
```
This runs the unit tests, mock LLM tests, and endpoint validation.

### Frontend Build Test
To verify the frontend builds successfully for production:
```bash
cd frontend
npm run build
```

## MLOps & Monitoring

- **Model Registry (MLflow):** The project uses MLflow to track model experiments and serve the deterministic baseline model (`chest-xray-vision-baseline`). Visit `http://localhost:5000` to view the registry.
- **Drift Monitoring (Evidently):** The API automatically logs input features during the `/scans` upload process. You can view drift reports by hitting the `GET /monitoring/drift` endpoint after sufficient data has been collected.

## Related Work

- **[CheXNet](https://stanfordmlgroup.github.io/projects/chexnet/)** (Stanford): one of the earlier deep learning models trained specifically on chest X-rays to detect pneumonia at a level comparable to practicing radiologists.
- **Google CXR Foundation** and various **CheXpert leaderboard** submissions: pushed performance further by training on hundreds of thousands of labeled scans.
- **[Aidoc](https://www.aidoc.com/)** and **[Viz.ai](https://www.viz.ai/)**: commercial products that already use AI to flag critical findings inside real radiology workflows.

## Datasets

- **[CheXpert](https://stanfordmlgroup.github.io/competitions/chexpert/)** (Stanford): 224,000+ chest X-rays with labels covering 14 pathologies, including uncertainty labels.
- **NIH ChestX-ray14**: 112,000 labeled images across the same 14 disease categories.

## Documentation

- [IDEA.md](IDEA.md): full system architecture, component breakdown, tech stack, team role details, and project timeline.
- [project_process_breakdown.md](project_process_breakdown.md): development timeline and task assignments.
