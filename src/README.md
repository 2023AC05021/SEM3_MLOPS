# Phase 2: Model Development & Experiment Tracking

## Overview
This phase focuses on machine learning model development with MLflow experiment tracking for the California Housing price prediction task. We implement baseline and advanced models, track experiments, and register the best performing model for production use.

## 🚀 Quick Start

### Prerequisites
```bash
# Install required packages
pip install mlflow pandas scikit-learn numpy pyyaml joblib

# Ensure your project structure looks like:
project_root/
├── data/
│   └── processed/
│       ├── train.csv
│       └── test.csv
├── src/
│   ├── config/
│   │   └── params.yml
│   ├── utils/
│   │   ├── __init__.py
│   │   └── data_loader.py
│   └── training/
│       └── train.py
├── models/                 # Will be created automatically
├── mlflow.db              # Will be created automatically
├── .gitignore
└── README.md
```

### Step-by-Step Execution

#### 1. Start MLflow Tracking Server
```bash
# From project root directory
mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./models/artifacts --host 127.0.0.1 --port 5000
```
- This starts the MLflow UI at `http://localhost:5000`
- Uses SQLite database for experiment metadata
- Stores model artifacts in `./models/artifacts/`
- Keep this terminal open while training

#### 2. Run Model Training
```bash
# From project root (in a new terminal)
python src/training/train.py
```

#### 3. View Results
- Open browser and go to `http://localhost:5000`
- View experiment runs, compare metrics, and explore model artifacts
- Check registered models in the "Models" tab

## 📁 Current Implementation

### Folder Structure
```
src/
├── config/                 # Configuration management
│   └── params.yml         # Project parameters (paths, model config, MLflow settings)
├── utils/                  # Utility functions
│   ├── __init__.py        # Package initialization
│   └── data_loader.py     # Data loading and preprocessing utilities
└── training/               # Training scripts
    └── train.py           # Main training script with MLflow tracking
```

### Key Components

#### Configuration (`src/config/params.yml`)
- **Data paths**: Training and test dataset locations
- **Model settings**: Model registry name, random state
- **MLflow config**: Experiment name and tracking settings

#### Data Utilities (`src/utils/data_loader.py`)
- **`load_data()`**: CSV file loading with error handling
- **`prepare_data()`**: Feature extraction, scaling, and preprocessing
- **Automatic feature detection**: Excludes ID and target columns dynamically
- **Data validation**: Missing value handling and data quality checks

#### Training Pipeline (`src/training/train.py`)
- **Experiment 1**: Linear Regression baseline model
- **Experiment 2**: Decision Tree Regressor with hyperparameters
- **MLflow Integration**: Automatic logging of metrics, parameters, and models
- **Model Registration**: Automatic registration of best performing model
- **Performance Tracking**: RMSE and R² score evaluation

## 🎯 Model Performance

The training script implements two models:

1. **Linear Regression (Baseline)**
   - Simple linear model for baseline comparison
   - Logs RMSE and R² metrics
   - Artifact path: `linear-reg-model`

2. **Decision Tree Regressor**
   - Hyperparameter: `max_depth=5`
   - Uses configured random state for reproducibility
   - Artifact path: `decision-tree-model`

**Automatic Best Model Selection**: The script automatically identifies and registers the model with the lowest RMSE in the MLflow Model Registry.

## 🔧 Configuration Details

### Data Configuration
```yaml
data:
  train_path: data/processed/train.csv    # Training dataset path
  test_path: data/processed/test.csv      # Test dataset path  
  target_col: target                      # Target column name
```

### Model Configuration
```yaml
model:
  name: california-housing-regressor      # MLflow Model Registry name
  random_state: 42                        # For reproducibility
```

### MLflow Configuration
```yaml
mlflow:
  experiment_name: California Housing Prediction  # Experiment name in MLflow
```

## 📊 Expected Output

When you run the training script, you'll see:

```
Starting MLflow experiment: California Housing Prediction
MLflow tracking URI: http://127.0.0.1:5000

Loading and preparing data...
Data loaded successfully from [path]/train.csv
Shape: (16512, 11)
...

==================================================
EXPERIMENT 1: LINEAR REGRESSION (BASELINE)
==================================================
Linear Regression - RMSE: 0.7423, R2: 0.5916

==================================================
EXPERIMENT 2: DECISION TREE REGRESSOR
==================================================
Decision Tree - RMSE: 0.7294, R2: 0.6053

==================================================
EXPERIMENT SUMMARY
==================================================
Linear Regression  - RMSE: 0.7423, R2: 0.5916
Decision Tree      - RMSE: 0.7294, R2: 0.6053

Best performing model: Decision Tree

============================================================
MODEL REGISTRATION
============================================================
Best performing run identified:
  Run ID: [run_id]
  Run Name: DecisionTree
  RMSE: 0.7294
  R2 Score: 0.6053

✅ Model successfully registered!
   Model Name: california-housing-regressor
   Model Version: 1
   Model Stage: None

🎯 FINAL SUMMARY:
   Best Model: DecisionTree
   Performance: RMSE=0.7294, R2=0.6053
   Registered as: california-housing-regressor v1
   Access via MLflow UI: http://127.0.0.1:5000
```

## 🔍 Troubleshooting

### Common Issues

1. **"Data file not found"**
   - Ensure your data files are in `data/processed/` directory
   - Check that column names match your dataset (especially target column)

2. **MLflow UI not accessible**
   - Verify MLflow server is running: `mlflow ui --backend-store-uri sqlite:///mlflow.db`
   - Check if port 5000 is available or use a different port

3. **Import errors**
   - Ensure all required packages are installed: `pip install mlflow pandas scikit-learn numpy pyyaml joblib`
   - Create empty `__init__.py` file in `src/utils/` directory

4. **Model registration fails**
   - Check MLflow server is running and accessible
   - Verify model artifacts were created successfully in previous steps

## 🚀 Next Steps

### Integration Points

#### From Previous Phase (Data):
- ✅ Load preprocessed datasets from `data/processed/`
- ✅ Automatic feature detection and preprocessing
- ✅ Data validation and quality checks

#### To Next Phase (API Development):
- ✅ Production-ready model registered in MLflow Model Registry
- ✅ Model loading utilities available (`mlflow.sklearn.load_model`)
- ✅ Model metadata and performance metrics tracked
- ✅ Versioned model artifacts accessible for serving

### Future Enhancements
- [ ] Hyperparameter tuning with Hyperopt
- [ ] Cross-validation implementation
- [ ] Additional model algorithms (Random Forest, XGBoost)
- [ ] Advanced feature engineering
- [ ] Model interpretability analysis
- [ ] Production model monitoring setup

## 📋 Dependencies

```txt
mlflow>=2.0.0
pandas>=1.3.0
scikit-learn>=1.0.0
numpy>=1.21.0
pyyaml>=6.0
joblib>=1.1.0
```

## 🔒 Git Configuration

The `.gitignore` file excludes:
- `mlflow.db` - Experiment database
- `models/` - Model artifacts directory
- `mlruns/` - MLflow runs directory
- Standard Python artifacts

**Note**: Each developer should maintain their own local MLflow tracking. For production, use remote MLflow tracking servers and artifact stores.