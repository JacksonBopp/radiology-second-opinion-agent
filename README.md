# Radiology Second-Opinion Agent

**Team:** The Nguyeners

## Team Members & Roles

| Member | Role |
|---|---|
| Jackson Bopp | Data & MLOps Engineer — data pipeline, model serving, infrastructure |
| Bryan Nguyen | GenAI & NLP Engineer — report generation, clinical language layer |
| Nicholas Toptchi | ML Vision Engineer — computer vision pipeline |
| Amrit Selva Ganesh | Agentic Systems Engineer & Full Stack/Integration Engineer — orchestration/reasoning layer, UI/API integration (supported by Jackson on the full-stack side) |

See [IDEA.md](IDEA.md) for the detailed breakdown of responsibilities, architecture, and tech stack for each role.

## Project Description

We are building a Radiology Second-Opinion Agent — an AI-powered system that analyzes medical images like chest X-rays and flags potential abnormalities, then generates a structured diagnostic report similar to what a radiologist would produce.

The system works in stages: a computer vision model trained to detect conditions like pneumonia, lung nodules, and other common pathologies analyzes the scan. An AI agent then takes those findings and cross-references them against similar historical cases and relevant medical literature. Finally, a large language model synthesizes everything into a readable report, complete with a ranked list of possible diagnoses and a confidence level attached to each one.

The goal is not to replace radiologists but to act as a reliable second opinion, particularly in scenarios where access to specialists may be limited.

## Related Work

- **[CheXNet](https://stanfordmlgroup.github.io/projects/chexnet/)** (Stanford) — one of the earlier deep learning models trained specifically on chest X-rays to detect pneumonia at a level comparable to practicing radiologists.
- **Google CXR Foundation** and various **CheXpert leaderboard** submissions — pushed performance further by training on hundreds of thousands of labeled scans.
- **[Aidoc](https://www.aidoc.com/)** and **[Viz.ai](https://www.viz.ai/)** — commercial products that already use AI to flag critical findings inside real radiology workflows, though both are closed proprietary systems.

What differentiates this project is that it does not just output a classification score. It combines the vision model with an agentic reasoning layer and a full report generation component, producing a more complete AI system rather than a standalone classifier.

## Datasets

- **[CheXpert](https://stanfordmlgroup.github.io/competitions/chexpert/)** (Stanford) — 224,000+ chest X-rays with labels covering 14 pathologies, including uncertainty labels for cases where expert radiologists disagreed. Useful for communicating uncertainty and confidence, which is a core goal of this project.
- **NIH ChestX-ray14** — a fully open supplemental dataset with 112,000 labeled images across the same 14 disease categories, used for additional training/evaluation variety.

## Documentation

- [IDEA.md](IDEA.md) — full system architecture, component breakdown, tech stack, team role details, and project timeline.
