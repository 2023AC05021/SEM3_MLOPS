# --- Resource Definition: S3 Bucket ---
# This block defines the S3 bucket we want to create.

resource "aws_s3_bucket" "my_local_bucket" {
  # Bucket names must be globally unique in real AWS, but are scoped
  # within your LocalStack instance. A unique suffix helps avoid collisions.
  bucket = "my-local-test-bucket-12345"

  tags = {
    Name        = "My Local Test Bucket"
    Environment = "Development"
  }
}


resource "aws_s3_object" "dvc_remote" {
  # Reference the bucket created earlier to ensure this object is placed inside it.
  bucket = aws_s3_bucket.my_local_bucket.id

  # The "path" of the folder. The trailing slash is essential.
  key    = "california_housing_dvc/"

  # We provide an empty content to create a zero-byte object.
  # This is a common technique for creating folder placeholders.
  content = ""

  # A tag to identify this object as a folder placeholder.
  tags = {
    Type = "Folder"
  }

  depends_on = [ aws_s3_bucket.my_local_bucket ]
}

# --- Resource Definition: EC2 Instance ---
# This block defines the EC2 instance to be launched.

data "aws_ami" "ubuntu" {
  # Find the most recent Ubuntu 20.04 LTS AMI available in the region.
  # LocalStack has a set of default AMIs available.
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web_server" {
  # The AMI to use for the instance. We reference the data source defined above.
  ami           = data.aws_ami.ubuntu.id

  # The instance type. t2.micro is usually available in LocalStack.
  instance_type = "t2.micro"

  # A key pair is not strictly required for LocalStack unless you intend to
  # test SSH access, which requires further setup.
  # key_name = "my-key-pair"

  tags = {
    Name = "Local-Web-Server"
  }
}