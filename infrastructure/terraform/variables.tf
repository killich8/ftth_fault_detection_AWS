variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "s3_bucket_name" {
  description = "Name of S3 bucket for data and models"
  type        = string
  default     = "ftth-fault-detection-data"
}

variable "ecr_repository_name" {
  description = "Name of ECR repository for Docker images"
  type        = string
  default     = "ftth-fault-detection"
}

variable "jenkins_ami" {
  description = "AMI ID for Jenkins server"
  type        = string
  default     = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (adjust as needed)
}

variable "jenkins_instance_type" {
  description = "Instance type for Jenkins server"
  type        = string
  default     = "t3.medium"
}

variable "api_ami" {
  description = "AMI ID for API server"
  type        = string
  default     = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (adjust as needed)
}

variable "api_instance_type" {
  description = "Instance type for API server"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of SSH key pair for EC2 instances"
  type        = string
  default     = "ftth-key-pair"
}
