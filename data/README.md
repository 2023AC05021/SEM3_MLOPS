# MLOps Project - California Housing Dataset

## Phase 1: Repository and Data Versioning COMPLETED

### Overview
This phase establishes the foundation for our MLOps project by setting up proper data versioning and preprocessing pipelines for the California Housing dataset. All data-related components are now properly version-controlled using DVC and Git.

## Implementation Status

#### Step 1 DVC Integration
- [x] DVC repository initialized with `dvc init`
- [x] Local DVC remote storage configured (`dvc_remote/` directory)
- [x] DVC cache directory properly configured and excluded from Git
- [x] Initial DVC configuration committed to repository

#### Step 2 Data Acquisition and Initial Processing
- [x] California Housing dataset fetched using `data/scripts/01_fetch_data.py`
- [x] Raw dataset saved as `data/raw/california_housing_raw.csv`
- [x] Comprehensive EDA notebook created (`data/notebooks/01_EDA.ipynb`)
- [x] Data schema and feature descriptions documented
- [x] Initial data quality validation completed

#### Step 3: Data Preprocessing Pipeline
- [x] Reproducible preprocessing pipeline (`data/scripts/02_preprocess_data.py`)
- [x] Feature engineering implemented (rooms_per_person feature)
- [x] Train/test splits created with proper random state (80/20 split)
- [x] Processed datasets saved as `train.csv` and `test.csv`
- [x] Command-line interface with configurable parameters

#### Step 4: Data Versioning
- [x] Raw data tracked with DVC (`data/raw/california_housing_raw.csv.dvc`)
- [x] Processed data tracked with DVC (`data/processed.dvc`)
- [x] All data pushed to DVC remote storage
- [x] DVC metadata files committed to Git repository

### Current Folder Structure
```
data/
├── raw/                           # Original California Housing dataset (DVC tracked)
│   └── california_housing_raw.csv # Raw dataset from sklearn
├── processed/                     # Train/test splits (DVC tracked)
│   ├── train.csv                 # Training set (80% of data)
│   └── test.csv                  # Test set (20% of data)
├── notebooks/                     # Data analysis and exploration
│   └── 01_EDA.ipynb              # Comprehensive EDA notebook
└── scripts/                       # Data processing scripts
    ├── 01_fetch_data.py          # Dataset acquisition script
    └── 02_preprocess_data.py     # Preprocessing pipeline

dvc_remote/                        # Local DVC remote storage
.dvc/                             # DVC configuration (cache excluded)
data/raw/california_housing_raw.csv.dvc    # DVC metadata for raw data
data/processed.dvc                          # DVC metadata for processed data
```

### Dataset Information

**California Housing Dataset**
- **Source**: sklearn.datasets.fetch_california_housing
- **Samples**: 20,640 housing blocks
- **Features**: 8 numerical features + 1 engineered feature
- **Target**: Median house value (in hundreds of thousands of dollars)

**Features**:
- `MedInc`: Median income in block group
- `HouseAge`: Median house age in block group  
- `AveRooms`: Average number of rooms per household
- `AveBedrms`: Average number of bedrooms per household
- `Population`: Block group population
- `AveOccup`: Average number of household members
- `Latitude`: Block group latitude
- `Longitude`: Block group longitude
- `rooms_per_person`: Engineered feature (AveRooms × AveOccup / Population)

### Usage Instructions

#### Running the Data Pipeline
```bash
# 1. Fetch raw data
python data/scripts/01_fetch_data.py

# 2. Preprocess data with default settings
python data/scripts/02_preprocess_data.py \
    --input-path data/raw/california_housing_raw.csv \
    --output-path data/processed

# 3. Preprocess with custom parameters
python data/scripts/02_preprocess_data.py \
    --input-path data/raw/california_housing_raw.csv \
    --output-path data/processed \
    --test-size 0.25 \
    --random-state 123 \
    --stratify
```

#### DVC Operations
```bash
# Pull data from remote (for new team members)
dvc pull

# Check data status
dvc status

# Push updated data to remote
dvc push
```

#### Exploratory Data Analysis
```bash
# Launch Jupyter notebook for EDA
jupyter lab data/notebooks/01_EDA.ipynb
```

### Key Achievements

**Data Quality**:
- No missing values detected in dataset
- All features are numerical and ready for ML
- Proper train/test splitting with reproducible random state
- Feature engineering successfully implemented

**Reproducibility**:
- All data operations are scripted and parameterized
- DVC ensures data version consistency across environments  
- Random states fixed for reproducible splits
- Complete data lineage documented

**Version Control**:
- Data files properly excluded from Git repository
- DVC metadata files tracked in Git
- Local DVC remote configured and functional
- Data integrity verified with checksums

### Integration Points

#### From Previous Phase: 
N/A (Initial phase)

#### To Next Phase (Model Development):
- Clean, version-controlled training data available in `data/processed/train.csv`
- Hold-out test set ready in `data/processed/test.csv`
- Data schema and feature documentation completed
- Preprocessing pipeline ready for model training integration
- DVC-tracked datasets accessible via `dvc pull`
- Feature engineering functions available for model deployment

### Technical Specifications

**Data Split**:
- Training Set: 16,512 samples (80%)
- Test Set: 4,128 samples (20%)
- Random State: 42 (configurable)
- Stratification: Optional based on target quartiles

**Performance Metrics**:
- Data Processing Time: < 5 seconds
- File Sizes: Raw (~1.6MB), Processed (~1.3MB total)
- Memory Usage: < 50MB peak

### Dependencies
```bash
# Core dependencies
pip install pandas>=1.3.0
pip install numpy>=1.21.0
pip install scikit-learn>=1.0.0
pip install matplotlib>=3.4.0
pip install seaborn>=0.11.0

# DVC and versioning
pip install dvc>=2.0.0

# Development
pip install jupyter>=1.0.0
pip install argparse  # (built-in with Python 3.2+)
```
