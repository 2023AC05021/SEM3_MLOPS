import os
import pandas as pd
from sklearn.datasets import fetch_california_housing
from pathlib import Path

def main():
    """
    Main function to fetch and save the California Housing dataset.
    """
    # Use the script's location to determine the project root and output directory
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent.absolute()
    output_dir = project_root / "raw"
    
    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {output_dir}")
    
    # Fetch the California Housing dataset
    print("Fetching California Housing dataset...")
    california_housing = fetch_california_housing()
    
    # Convert features to DataFrame
    features_df = pd.DataFrame(
        california_housing.data, 
        columns=california_housing.feature_names
    )
    
    # Add the target variable to the DataFrame
    features_df['target'] = california_housing.target
    
    # Display basic information about the dataset
    print(f"Dataset shape: {features_df.shape}")
    print(f"Features: {list(california_housing.feature_names)}")
    print(f"Target variable: median house value (in hundreds of thousands of dollars)")
    
    # Save the DataFrame to CSV file, including the index
    output_path = output_dir / "california_housing_raw.csv"
    features_df.to_csv(output_path, index=False)
    
    print(f"Dataset saved successfully to: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    
    # Display first few rows as confirmation
    print("\nFirst 5 rows of the dataset:")
    print(features_df.head())
    
    # Display basic statistics
    print("\nDataset info:")
    print(features_df.info())

if __name__ == "__main__":
    main()