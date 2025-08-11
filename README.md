# MLOps California Housing Project


This repository demonstrates a complete MLOps workflow for the California Housing regression task using open-source tools. The system implements data versioning, experiment tracking, model deployment, CI/CD, and monitoring, as required by the assignment.

---

## MLOps Assignment - Group 10
- Shaik Asief Hussain - 2023ac05021
- BHOIRA MARIYAM YUSUF - 2023ac05328
- MOHAMMED FAISEL SAIT - 2023aa05525
- KHUNZA MERAJ - 2023ad05120

---

## System Architecture

**System flow is illustrated in [`mlops-flow-diagram.md`](mlops-flow-diagram.md)** (Mermaid diagram).

---

## Reference Document

For the detailed multi-phase system design and technology rationale, see [`mlops-housing-project.md`](mlops-housing-project.md).

---

## Assignment Criteria Mapping

| Assignment Task                                                  | Repository Locations      | Toolchain                        |
|------------------------------------------------------------------|--------------------------|----------------------------------|
| **Part 1: Repo & Data Versioning**                               | `data/`, root            | GitHub, DVC, pandas              |
| **Part 2: Model Development, Experiment Tracking**               | `src/`, `models/`        | MLflow, scikit-learn, Jupyter    |
| **Part 3: API & Docker Packaging**                               | `api/`, `deployment/`    | FastAPI, Pydantic, Docker        |
| **Part 4: CI/CD with GitHub Actions**                            | `.github/workflows/`     | GitHub Actions, Docker Hub, AWS  |
| **Part 5: Logging and Monitoring**                               | `monitoring/`            | Prometheus, Grafana, SQLite      |
| **Part 6: Summary & Demo**                                       | root, `docs/`            | Markdown, Video, Diagrams        |
| **Bonus: Validation, Dashboards, Retraining**                    | `api/`, `monitoring/`, `src/` | Pydantic, Prometheus, MLflow    |

---

## Toolchain & Workflow

- **GitHub**: Version control & CI/CD trigger.
- **DVC**: Tracks datasets, ensures reproducibility.
- **MLflow**: Tracks/model experiments, manages model versioning.
- **FastAPI + Pydantic**: Serves predictions with validation.
- **Docker/Docker Hub**: Provides consistent deployment artifacts.
- **GitHub Actions**: Automates testing, building, deployment.
- **Prometheus + Grafana**: Monitors metrics, supports custom dashboards.
- **SQLite**: Stores API request logs.
- **AWS EC2/LocalStack**: Flexible deployment targets.

**End-to-end flow:**  
Data is versioned and preprocessed → Models are trained/experimented via MLflow → Best models are exposed via a containerized API → CI/CD pipelines automate validation, building, and deployment → Monitoring and logging provide operational observability.

---

## Folder Overview

- `data/`: Raw/processed data, DVC, notebooks.
- `src/`: Model development, training, experiment tracking.
- `models/`: Trained model artifacts and metadata.
- `api/`: Inference API (FastAPI), validation, Docker configs.
- `monitoring/`: Metrics/alerting/visualization configurations.
- `.github/workflows/`: All CI/CD workflow files.
- `deployment/`: Infra-as-code, deploy scripts, env config.

**See each folder’s README.md for phase tasks and integration details.**

---

## Quick Start

1. See [`mlops-housing-project.md`](mlops-housing-project.md) for architecture/guidance.
2. Navigate to each folder’s README.md for implementation instructions and integration steps.

---