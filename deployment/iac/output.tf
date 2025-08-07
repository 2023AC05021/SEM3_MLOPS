# --- Outputs ---
# These outputs will display useful information after `terraform apply` completes.

output "s3_bucket_name" {
  description = "The name of the created S3 bucket."
  value       = aws_s3_bucket.my_local_bucket.bucket
}

output "ec2_instance_id" {
  description = "The ID of the created EC2 instance."
  value       = aws_instance.web_server.id
}

output "ec2_instance_ami" {
  description = "The AMI used for the EC2 instance."
  value       = aws_instance.web_server.ami
}
