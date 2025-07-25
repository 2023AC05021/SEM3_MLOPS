```mermaid
    graph TD
    A[Developer] -->|Push Code| B[GitHub Repository]
    B --> C[GitHub Actions CI/CD]
    
    D[California Housing Dataset] -->|Track with| E[DVC]
    E -->|Version Control| B
    
    B -->|Code Changes| F[Data Preprocessing]
    F -->|Clean Data| G[Model Training]
    
    G -->|Linear Regression<br/>Decision Tree| H[MLflow Tracking]
    H -->|Log Experiments| I[MLflow Model Registry]
    I -->|Best Model| J[Model Selection]
    
    C -->|Trigger Build| K[Docker Build]
    J -->|Model Artifacts| L[FastAPI Application]
    L -->|Input Validation| M[Pydantic Schemas]
    
    K -->|Container Image| N[Docker Hub Registry]
    N -->|Pull Image| O[Deployment Target]
    
    O -->|AWS EC2| P[Production Environment]
    O -->|Local| Q[LocalStack]
    
    L -->|Prediction API| R[/predict Endpoint]
    R -->|JSON Input/Output| S[Model Inference]
    
    S -->|Log Requests| T[SQLite Database]
    S -->|Expose Metrics| U[Prometheus Metrics]
    
    U -->|Scrape Data| V[Prometheus Server]
    V -->|Query Metrics| W[Grafana Dashboard]
    
    T -->|Log Analysis| X[Application Logs]
    W -->|Visualize| Y[Monitoring Dashboard]
    
    C -->|Run Tests| Z[Pytest Suite]
    C -->|Code Quality| AA[Black + Flake8]
    
    BB[Model Performance] -->|Trigger| CC[Automated Retraining]
    CC -->|New Model| I
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style H fill:#fff3e0
    style L fill:#e8f5e8
    style V fill:#ffebee
    style W fill:#f1f8e9
```
