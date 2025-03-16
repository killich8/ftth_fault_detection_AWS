variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "s3_bucket_prefix" {
  description = "Prefix for S3 bucket names"
  type        = string
  default     = "ftth-fault-detection"
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

variable "training_ami" {
  description = "AMI ID for training instances"
  type        = string
  default     = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (adjust as needed)
}

variable "training_instance_type" {
  description = "Instance type for model training"
  type        = string
  default     = "g4dn.xlarge"  # GPU instance for ML training
}

variable "key_name" {
  description = "Name of SSH key pair for EC2 instances"
  type        = string
  default     = "ftth-key-pair"
}
