"""
Data loading and preparation utilities for California Housing MLOps project.
This module provides functions to load data and prepare train/test splits.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os


def load_data(file_path):
    """
    Load data from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded dataframe
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: For other loading errors
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        data = pd.read_csv(file_path)
        print(f"Data loaded successfully from {file_path}")
        print(f"Shape: {data.shape}")
        
        return data
        
    except Exception as e:
        print(f"Error loading data from {file_path}: {str(e)}")
        raise


def prepare_data(train_data, test_data, target_col, scale_features=True, id_col='ID'):
    """
    Prepare training and testing data by separating features and target.
    Automatically identifies and excludes non-feature columns (ID, target).
    
    Args:
        train_data (pd.DataFrame): Training dataset
        test_data (pd.DataFrame): Testing dataset  
        target_col (str): Name of the target column
        scale_features (bool): Whether to scale features using StandardScaler
        id_col (str): Name of the ID column to exclude from features
        
    Returns:
        tuple: (X_train, y_train, X_test, y_test)
        
    Raises:
        KeyError: If target column is not found in the data
        ValueError: If data preparation fails
    """
    try:
        # Check if target column exists
        if target_col not in train_data.columns:
            raise KeyError(f"Target column '{target_col}' not found in training data")
        if target_col not in test_data.columns:
            raise KeyError(f"Target column '{target_col}' not found in test data")
        
        # Identify columns to exclude from features
        exclude_cols = [target_col]
        if id_col in train_data.columns:
            exclude_cols.append(id_col)
            print(f"Excluding ID column: {id_col}")
        
        # Get feature column names (all columns except target and ID)
        feature_cols = [col for col in train_data.columns if col not in exclude_cols]
        print(f"Feature columns identified: {feature_cols}")
        print(f"Number of features: {len(feature_cols)}")
            
        # Separate features and target
        X_train = train_data[feature_cols].copy()
        y_train = train_data[target_col].copy()
        
        X_test = test_data[feature_cols].copy()
        y_test = test_data[target_col].copy()
        
        # Handle missing values if any
        missing_train = X_train.isnull().sum().sum()
        missing_test = X_test.isnull().sum().sum()
        
        if missing_train > 0:
            print(f"Warning: {missing_train} missing values found in training features. Filling with median.")
            # Fill missing values with median for numeric columns
            numeric_cols = X_train.select_dtypes(include=[np.number]).columns
            X_train[numeric_cols] = X_train[numeric_cols].fillna(X_train[numeric_cols].median())
            
        if missing_test > 0:
            print(f"Warning: {missing_test} missing values found in test features. Filling with training median.")
            # Use training data median for test data
            numeric_cols = X_test.select_dtypes(include=[np.number]).columns
            train_medians = X_train[numeric_cols].median()
            X_test[numeric_cols] = X_test[numeric_cols].fillna(train_medians)
        
        # Scale features if requested
        if scale_features:
            # Only scale numeric features
            numeric_cols = X_train.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) > 0:
                scaler = StandardScaler()
                X_train_scaled = X_train.copy()
                X_test_scaled = X_test.copy()
                
                # Scale only numeric columns
                X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
                X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])
                
                X_train = X_train_scaled
                X_test = X_test_scaled
                
                print(f"Scaled {len(numeric_cols)} numeric features using StandardScaler")
            else:
                print("No numeric features found to scale")
        
        # Display feature statistics
        print(f"\nData preparation completed:")
        print(f"  X_train shape: {X_train.shape}")
        print(f"  y_train shape: {y_train.shape}")
        print(f"  X_test shape: {X_test.shape}")
        print(f"  y_test shape: {y_test.shape}")
        
        # Show feature ranges after scaling
        if scale_features and len(X_train.select_dtypes(include=[np.number]).columns) > 0:
            print(f"  Feature ranges after scaling:")
            numeric_features = X_train.select_dtypes(include=[np.number])
            print(f"    Min: {numeric_features.min().min():.4f}")
            print(f"    Max: {numeric_features.max().max():.4f}")
            print(f"    Mean: {numeric_features.mean().mean():.4f}")
        
        return X_train, y_train, X_test, y_test
        
    except Exception as e:
        print(f"Error preparing data: {str(e)}")
        raise


def load_and_split_data(file_path, target_col, test_size=0.2, random_state=42, scale_features=True):
    """
    Load data from a single file and split into train/test sets.
    Alternative function if you have a single dataset file instead of pre-split files.
    
    Args:
        file_path (str): Path to the CSV file
        target_col (str): Name of the target column
        test_size (float): Proportion of data to use for testing (default: 0.2)
        random_state (int): Random state for reproducible splits
        scale_features (bool): Whether to scale features using StandardScaler
        
    Returns:
        tuple: (X_train, y_train, X_test, y_test)
    """
    try:
        # Load the data
        data = load_data(file_path)
        
        # Separate features and target
        if target_col not in data.columns:
            raise KeyError(f"Target column '{target_col}' not found in data")
            
        X = data.drop(columns=[target_col])
        y = data[target_col]
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Handle missing values if any
        if X_train.isnull().sum().sum() > 0:
            print("Warning: Missing values found. Filling with median.")
            X_train = X_train.fillna(X_train.median())
            X_test = X_test.fillna(X_train.median())  # Use training median for test set
        
        # Scale features if requested
        if scale_features:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Convert back to DataFrame
            X_train = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
            X_test = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
            
            print("Features scaled using StandardScaler")
        
        print(f"Data loaded and split:")
        print(f"  X_train shape: {X_train.shape}")
        print(f"  y_train shape: {y_train.shape}")
        print(f"  X_test shape: {X_test.shape}")
        print(f"  y_test shape: {y_test.shape}")
        
        return X_train, y_train, X_test, y_test
        
    except Exception as e:
        print(f"Error in load_and_split_data: {str(e)}")
        raise


def get_data_info(data):
    """
    Get basic information about the dataset.
    
    Args:
        data (pd.DataFrame): Dataset to analyze
        
    Returns:
        dict: Dictionary containing data information
    """
    info = {
        'shape': data.shape,
        'columns': list(data.columns),
        'dtypes': data.dtypes.to_dict(),
        'missing_values': data.isnull().sum().to_dict(),
        'numeric_columns': list(data.select_dtypes(include=[np.number]).columns),
        'categorical_columns': list(data.select_dtypes(include=['object']).columns)
    }
    
    return info


def validate_data(data, target_col):
    """
    Validate the dataset for common issues.
    
    Args:
        data (pd.DataFrame): Dataset to validate
        target_col (str): Name of the target column
        
    Returns:
        dict: Dictionary containing validation results
    """
    validation_results = {
        'is_valid': True,
        'issues': []
    }
    
    # Check if target column exists
    if target_col not in data.columns:
        validation_results['is_valid'] = False
        validation_results['issues'].append(f"Target column '{target_col}' not found")
    
    # Check for empty dataset
    if data.empty:
        validation_results['is_valid'] = False
        validation_results['issues'].append("Dataset is empty")
    
    # Check for duplicate rows
    duplicates = data.duplicated().sum()
    if duplicates > 0:
        validation_results['issues'].append(f"Found {duplicates} duplicate rows")
    
    # Check for missing values in target
    if target_col in data.columns:
        target_missing = data[target_col].isnull().sum()
        if target_missing > 0:
            validation_results['is_valid'] = False
            validation_results['issues'].append(f"Found {target_missing} missing values in target column")
    
    return validation_results