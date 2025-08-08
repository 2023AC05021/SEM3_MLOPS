#!/usr/bin/env python3
"""
Data Preprocessing Pipeline for California Housing Dataset

This script performs reproducible data preprocessing including:
1. Feature engineering (rooms_per_person)
2. Train/test splitting with stratification
3. Data validation and saving

Author: MLOps Project
Date: 2025
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from pathlib import Path


def parse_arguments():
    """
    Parse command line arguments for the preprocessing pipeline.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Preprocess California Housing dataset for ML pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input-path",
        type=str,
        required=True,
        help="Path to the raw CSV file (e.g., data/raw/california_housing_raw.csv)"
    )
    
    parser.add_argument(
        "--output-path",
        type=str,
        required=True,
        help="Directory path for processed data output (e.g., data/processed)"
    )
    
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of dataset to include in test split"
    )
    
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducible train/test splitting"
    )
    
    parser.add_argument(
        "--stratify",
        action="store_true",
        help="Whether to stratify the split based on target variable quartiles"
    )
    
    return parser.parse_args()


def validate_input_file(input_path):
    """
    Validate that the input file exists and is readable.
    
    Args:
        input_path (str): Path to input CSV file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file is not a CSV file
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not input_path.lower().endswith('.csv'):
        raise ValueError(f"Input file must be a CSV file: {input_path}")
    
    print(f"✅ Input file validated: {input_path}")


def load_data(input_path):
    """
    Load data from CSV file with error handling.
    
    Args:
        input_path (str): Path to input CSV file
        
    Returns:
        pd.DataFrame: Loaded dataset
    """
    try:
        df = pd.read_csv(input_path)
        print(f"📊 Data loaded successfully: {df.shape[0]:,} rows × {df.shape[1]} columns")
        return df
    except Exception as e:
        raise RuntimeError(f"Error loading data from {input_path}: {str(e)}")


def engineer_features(df):
    """
    Perform feature engineering on the dataset.
    
    Args:
        df (pd.DataFrame): Input dataset
        
    Returns:
        pd.DataFrame: Dataset with engineered features
    """
    print("🔧 Starting feature engineering...")
    
    # Create a copy to avoid modifying original data
    df_processed = df.copy()
    
    # Feature engineering: rooms_per_person
    # Handle division by zero by replacing zero population with small value
    population_safe = df_processed['Population'].replace(0, 1)
    df_processed['rooms_per_person'] = df_processed['AveRooms'] * df_processed['AveOccup'] / population_safe
    
    # Additional feature engineering steps can be added here
    # For example:
    # df_processed['bedrooms_per_room'] = df_processed['AveBedrms'] / df_processed['AveRooms']
    # df_processed['population_density'] = df_processed['Population'] / (some area measure)
    
    # Validate the new feature
    if df_processed['rooms_per_person'].isnull().any():
        print("Warning: NaN values detected in rooms_per_person feature")
        # Handle NaN values if any
        df_processed['rooms_per_person'].fillna(df_processed['rooms_per_person'].median(), inplace=True)
    
    print(f"Feature engineering completed. New shape: {df_processed.shape}")
    print(f"Created features: rooms_per_person")
    print(f"   - Mean: {df_processed['rooms_per_person'].mean():.3f}")
    print(f"   - Median: {df_processed['rooms_per_person'].median():.3f}")
    print(f"   - Range: {df_processed['rooms_per_person'].min():.3f} - {df_processed['rooms_per_person'].max():.3f}")
    
    return df_processed


def create_stratification_groups(target_series, n_groups=5):
    """
    Create stratification groups based on target variable quantiles.
    
    Args:
        target_series (pd.Series): Target variable
        n_groups (int): Number of stratification groups
        
    Returns:
        pd.Series: Stratification labels
    """
    return pd.qcut(target_series, q=n_groups, labels=False, duplicates='drop')


def split_data(df, test_size=0.2, random_state=42, stratify=False):
    """
    Split dataset into training and testing sets.
    
    Args:
        df (pd.DataFrame): Dataset to split
        test_size (float): Proportion for test set
        random_state (int): Random seed for reproducibility
        stratify (bool): Whether to stratify split
        
    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    print(f"Splitting data (train: {1-test_size:.0%}, test: {test_size:.0%})...")
    
    # Separate features and target
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Create stratification groups if requested
    stratify_labels = None
    if stratify:
        try:
            stratify_labels = create_stratification_groups(y)
            print("Using stratified sampling based on target quartiles")
        except Exception as e:
            print(f" Warning: Could not create stratification groups: {e}")
            print("   Proceeding with random sampling")
    
    # Perform train/test split
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_labels
        )
        
        print(f"Data split completed:")
        print(f"   - Training set: {X_train.shape[0]:,} samples")
        print(f"   - Test set: {X_test.shape[0]:,} samples")
        print(f"   - Features: {X_train.shape[1]} columns")
        
        # Combine features and target for each set
        train_df = pd.concat([X_train, y_train], axis=1)
        test_df = pd.concat([X_test, y_test], axis=1)
        
        return train_df, test_df
        
    except Exception as e:
        raise RuntimeError(f"Error during train/test split: {str(e)}")


def create_output_directory(output_path):
    """
    Create output directory if it doesn't exist.
    
    Args:
        output_path (str): Path to output directory
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    print(f"Output directory ready: {output_path}")


def save_processed_data(train_df, test_df, output_path):
    """
    Save processed training and testing datasets.
    
    Args:
        train_df (pd.DataFrame): Training dataset
        test_df (pd.DataFrame): Testing dataset
        output_path (str): Output directory path
    """
    print("💾 Saving processed datasets...")
    
    try:
        # Define output file paths
        train_path = os.path.join(output_path, 'train.csv')
        test_path = os.path.join(output_path, 'test.csv')
        
        # Save datasets
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        # Verify files were created and get their sizes
        train_size = os.path.getsize(train_path)
        test_size = os.path.getsize(test_path)
        
        print(f"Datasets saved successfully:")
        print(f"   - Training data: {train_path} ({train_size:,} bytes)")
        print(f"   - Test data: {test_path} ({test_size:,} bytes)")
        
        return train_path, test_path
        
    except Exception as e:
        raise RuntimeError(f"Error saving processed data: {str(e)}")


def print_data_summary(train_df, test_df):
    """
    Print summary statistics for the processed datasets.
    
    Args:
        train_df (pd.DataFrame): Training dataset
        test_df (pd.DataFrame): Testing dataset
    """
    print("\n" + "="*60)
    print("DATA PROCESSING SUMMARY")
    print("="*60)
    
    print(f"Training Set:")
    print(f"  Shape: {train_df.shape}")
    print(f"  Target mean: {train_df['target'].mean():.3f}")
    print(f"  Target std: {train_df['target'].std():.3f}")
    
    print(f"\nTest Set:")
    print(f"  Shape: {test_df.shape}")
    print(f"  Target mean: {test_df['target'].mean():.3f}")
    print(f"  Target std: {test_df['target'].std():.3f}")
    
    print(f"\nFeatures: {list(train_df.drop('target', axis=1).columns)}")
    
    # Check for any data leakage indicators
    train_target_range = (train_df['target'].min(), train_df['target'].max())
    test_target_range = (test_df['target'].min(), test_df['target'].max())
    
    print(f"\nTarget Range Validation:")
    print(f"  Train: {train_target_range[0]:.3f} - {train_target_range[1]:.3f}")
    print(f"  Test:  {test_target_range[0]:.3f} - {test_target_range[1]:.3f}")


def main():
    """
    Main function to orchestrate the data preprocessing pipeline.
    """
    print("🚀 Starting Data Preprocessing Pipeline")
    print("="*50)
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print(f"Configuration:")
        print(f"  Input path: {args.input_path}")
        print(f"  Output path: {args.output_path}")
        print(f"  Test size: {args.test_size}")
        print(f"  Random state: {args.random_state}")
        print(f"  Stratify: {args.stratify}")
        print()
        
        # Validate input file
        validate_input_file(args.input_path)
        
        # Load data
        df = load_data(args.input_path)
        
        # Perform feature engineering
        df_processed = engineer_features(df)
        
        # Split data into train/test sets
        train_df, test_df = split_data(
            df_processed,
            test_size=args.test_size,
            random_state=args.random_state,
            stratify=args.stratify
        )
        
        # Create output directory
        create_output_directory(args.output_path)
        
        # Save processed data
        train_path, test_path = save_processed_data(train_df, test_df, args.output_path)
        
        # Print summary
        print_data_summary(train_df, test_df)
        
        print(f"\nData preprocessing completed successfully!")
        print(f"Output files: {train_path}, {test_path}")
        
    except Exception as e:
        print(f"Error in preprocessing pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()