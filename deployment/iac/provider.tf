terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  # The region where resources will be created in LocalStack.
  region                      = "us-east-1"
  # Dummy credentials for LocalStack.
  access_key                  = "test"
  secret_key                  = "test"

  # These settings are crucial for making the provider work with LocalStack.
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true # Required for S3 endpoint routing in LocalStack

  # Override default AWS service endpoints to point to LocalStack's edge service.
  # The edge service listens on port 4566 by default.
  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
    sts = "http://localhost:4566" # STS is often used for authentication checks
  }
}