# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
}

# Terraform Backend Configuration
terraform {
  backend "s3" {
    bucket = "ftth-terraform-state"
    key    = "ftth-fault-detection/terraform.tfstate"
    region = "us-east-1"
  }
}

# Random ID for unique resource naming
resource "random_id" "suffix" {
  byte_length = 4
}

# VPC Configuration
resource "aws_vpc" "ftth_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "ftth-vpc-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "ftth_igw" {
  vpc_id = aws_vpc.ftth_vpc.id

  tags = {
    Name        = "ftth-igw-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Public Subnets
resource "aws_subnet" "public_subnet" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.ftth_vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "ftth-public-subnet-${count.index}-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Private Subnets
resource "aws_subnet" "private_subnet" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.ftth_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name        = "ftth-private-subnet-${count.index}-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# NAT Gateway for Private Subnets
resource "aws_eip" "nat_eip" {
  domain = "vpc"

  tags = {
    Name        = "ftth-nat-eip-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_nat_gateway" "ftth_nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnet[0].id

  tags = {
    Name        = "ftth-nat-gateway-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }

  depends_on = [aws_internet_gateway.ftth_igw]
}

# Route Tables
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.ftth_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ftth_igw.id
  }

  tags = {
    Name        = "ftth-public-rt-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.ftth_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.ftth_nat.id
  }

  tags = {
    Name        = "ftth-private-rt-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_rta" {
  count          = length(aws_subnet.public_subnet)
  subnet_id      = aws_subnet.public_subnet[count.index].id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "private_rta" {
  count          = length(aws_subnet.private_subnet)
  subnet_id      = aws_subnet.private_subnet[count.index].id
  route_table_id = aws_route_table.private_route_table.id
}

# S3 Bucket for Data and Models
resource "aws_s3_bucket" "ftth_data_bucket" {
  bucket = "${var.s3_bucket_prefix}-data-${random_id.suffix.hex}"

  tags = {
    Name        = "${var.s3_bucket_prefix}-data-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_s3_bucket_versioning" "ftth_data_versioning" {
  bucket = aws_s3_bucket.ftth_data_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ftth_data_encryption" {
  bucket = aws_s3_bucket.ftth_data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ECR Repository for Docker Images
resource "aws_ecr_repository" "ftth_ecr" {
  name                 = "${var.ecr_repository_name}-${random_id.suffix.hex}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.ecr_repository_name}-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Security Groups
resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-sg-${random_id.suffix.hex}"
  description = "Security group for Jenkins server"
  vpc_id      = aws_vpc.ftth_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "jenkins-sg-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_security_group" "api_sg" {
  name        = "api-sg-${random_id.suffix.hex}"
  description = "Security group for API server"
  vpc_id      = aws_vpc.ftth_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "api-sg-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_security_group" "training_sg" {
  name        = "training-sg-${random_id.suffix.hex}"
  description = "Security group for model training instances"
  vpc_id      = aws_vpc.ftth_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "training-sg-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# IAM Roles and Policies
resource "aws_iam_role" "ec2_role" {
  name = "ftth-ec2-role-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "ftth-ec2-role-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_iam_policy" "s3_access_policy" {
  name        = "ftth-s3-access-policy-${random_id.suffix.hex}"
  description = "Policy for S3 access for FTTH fault detection"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.ftth_data_bucket.arn}",
          "${aws_s3_bucket.ftth_data_bucket.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "ftth-s3-access-policy-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_iam_policy" "ecr_access_policy" {
  name        = "ftth-ecr-access-policy-${random_id.suffix.hex}"
  description = "Policy for ECR access for FTTH fault detection"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:GetAuthorizationToken"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "ftth-ecr-access-policy-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_iam_role_policy_attachment" "s3_access_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "ecr_access_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ecr_access_policy.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ftth-ec2-profile-${random_id.suffix.hex}"
  role = aws_iam_role.ec2_role.name

  tags = {
    Name        = "ftth-ec2-profile-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# EC2 Instances
resource "aws_instance" "jenkins_server" {
  ami                    = var.jenkins_ami
  instance_type          = var.jenkins_instance_type
  subnet_id              = aws_subnet.public_subnet[0].id
  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name        = "ftth-jenkins-server-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_instance" "api_server" {
  ami                    = var.api_ami
  instance_type          = var.api_instance_type
  subnet_id              = aws_subnet.public_subnet[0].id
  vpc_security_group_ids = [aws_security_group.api_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name        = "ftth-api-server-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Launch Template for Training Instances
resource "aws_launch_template" "training_template" {
  name_prefix   = "ftth-training-"
  image_id      = var.training_ami
  instance_type = var.training_instance_type
  key_name      = var.key_name

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.training_sg.id]
  }

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      volume_size = 50
      volume_type = "gp3"
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name        = "ftth-training-instance"
      Environment = var.environment
      Project     = "FTTH Fault Detection"
    }
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y python3-pip git
    pip3 install tensorflow numpy pandas scikit-learn matplotlib seaborn boto3
    mkdir -p /opt/ftth
    cd /opt/ftth
    aws s3 cp s3://${aws_s3_bucket.ftth_data_bucket.id}/code/training.zip .
    unzip training.zip
    chmod +x train.sh
    ./train.sh
  EOF
  )
}

# Load Balancer for API
resource "aws_lb" "api_lb" {
  name               = "ftth-api-lb-${random_id.suffix.hex}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.api_sg.id]
  subnets            = aws_subnet.public_subnet[*].id

  tags = {
    Name        = "ftth-api-lb-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_lb_target_group" "api_tg" {
  name     = "ftth-api-tg-${random_id.suffix.hex}"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.ftth_vpc.id

  health_check {
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }

  tags = {
    Name        = "ftth-api-tg-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

resource "aws_lb_target_group_attachment" "api_tg_attachment" {
  target_group_arn = aws_lb_target_group.api_tg.arn
  target_id        = aws_instance.api_server.id
  port             = 8000
}

resource "aws_lb_listener" "api_listener" {
  load_balancer_arn = aws_lb.api_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_tg.arn
  }

  tags = {
    Name        = "ftth-api-listener-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "api_cpu_alarm" {
  alarm_name          = "ftth-api-cpu-alarm-${random_id.suffix.hex}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors API server CPU utilization"
  alarm_actions       = []

  dimensions = {
    InstanceId = aws_instance.api_server.id
  }

  tags = {
    Name        = "ftth-api-cpu-alarm-${random_id.suffix.hex}"
    Environment = var.environment
    Project     = "FTTH Fault Detection"
  }
}

# Outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.ftth_vpc.id
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket for data and models"
  value       = aws_s3_bucket.ftth_data_bucket.id
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = aws_ecr_repository.ftth_ecr.repository_url
}

output "jenkins_server_public_ip" {
  description = "The public IP of the Jenkins server"
  value       = aws_instance.jenkins_server.public_ip
}

output "api_server_public_ip" {
  description = "The public IP of the API server"
  value       = aws_instance.api_server.public_ip
}

output "api_load_balancer_dns" {
  description = "The DNS name of the API load balancer"
  value       = aws_lb.api_lb.dns_name
}
