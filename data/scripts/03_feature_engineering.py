#!/usr/bin/env python3
"""
Feature Engineering Pipeline for California Housing Dataset

This script performs feature engineering on the raw dataset:
1. Creates rooms_per_person feature
2. Validates engineered features
3. Saves feature-engineered dataset

Author: MLOps Project
Date: 2025
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path


def parse_arguments():
    """
    Parse command line arguments for feature engineering.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Apply feature engineering to California Housing dataset",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input-path",
        type=str,
        required=True,
        help="Path to the raw CSV file"
    )
    
    parser.add_argument(
        "--output-path",
        type=str,
        required=True,
        help="Path for the feature-engineered CSV output"
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
        df = pd.read_csv(input_path, index_col=0)
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
    
    # Validate the new feature
    if df_processed['rooms_per_person'].isnull().any():
        print("⚠️  Warning: NaN values detected in rooms_per_person feature")
        # Handle NaN values if any
        df_processed['rooms_per_person'].fillna(df_processed['rooms_per_person'].median(), inplace=True)
    
    print(f"✅ Feature engineering completed. New shape: {df_processed.shape}")
    print(f"📈 Created features: rooms_per_person")
    print(f"   - Mean: {df_processed['rooms_per_person'].mean():.3f}")
    print(f"   - Median: {df_processed['rooms_per_person'].median():.3f}")
    print(f"   - Range: {df_processed['rooms_per_person'].min():.3f} - {df_processed['rooms_per_person'].max():.3f}")
    
    return df_processed


def create_output_directory(output_path):
    """
    Create output directory if it doesn't exist.
    
    Args:
        output_path (str): Path to output file (directory will be created)
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory ready: {output_dir}")


def save_engineered_data(df, output_path):
    """
    Save feature-engineered dataset.
    
    Args:
        df (pd.DataFrame): Feature-engineered dataset
        output_path (str): Output file path
    """
    print("💾 Saving feature-engineered dataset...")
    
    try:
        df.to_csv(output_path, index=True)
        
        # Verify file was created and get its size
        file_size = os.path.getsize(output_path)
        
        print(f"✅ Feature-engineered dataset saved: {output_path}")
        print(f"   - File size: {file_size:,} bytes")
        print(f"   - Shape: {df.shape}")
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Error saving feature-engineered data: {str(e)}")


def print_feature_summary(df_original, df_engineered):
    """
    Print summary of feature engineering changes.
    
    Args:
        df_original (pd.DataFrame): Original dataset
        df_engineered (pd.DataFrame): Feature-engineered dataset
    """
    print("\n" + "="*50)
    print("📋 FEATURE ENGINEERING SUMMARY")
    print("="*50)
    
    print(f"Original features: {df_original.shape[1]}")
    print(f"Engineered features: {df_engineered.shape[1]}")
    print(f"New features added: {df_engineered.shape[1] - df_original.shape[1]}")
    
    new_features = set(df_engineered.columns) - set(df_original.columns)
    if new_features:
        print(f"New feature(s): {list(new_features)}")
    
    print(f"Dataset shape: {df_engineered.shape[0]:,} rows × {df_engineered.shape[1]} columns")


def main():
    """
    Main function to orchestrate the feature engineering pipeline.
    """
    print("🚀 Starting Feature Engineering Pipeline")
    print("="*50)
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print(f"Configuration:")
        print(f"  Input path: {args.input_path}")
        print(f"  Output path: {args.output_path}")
        print()
        
        # Validate input file
        validate_input_file(args.input_path)
        
        # Load data
        df_original = load_data(args.input_path)
        
        # Perform feature engineering
        df_engineered = engineer_features(df_original)
        
        # Create output directory
        create_output_directory(args.output_path)
        
        # Save feature-engineered data
        output_path = save_engineered_data(df_engineered, args.output_path)
        
        # Print summary
        print_feature_summary(df_original, df_engineered)
        
        print(f"\n🎉 Feature engineering completed successfully!")
        print(f"Output file: {output_path}")
        
    except Exception as e:
        print(f"❌ Error in feature engineering pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()