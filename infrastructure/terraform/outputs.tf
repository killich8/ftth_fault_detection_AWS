# Terraform Output Values
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.ftth_vpc.id
}

output "public_subnet_ids" {
  description = "The IDs of the public subnets"
  value       = aws_subnet.public_subnet[*].id
}

output "private_subnet_ids" {
  description = "The IDs of the private subnets"
  value       = aws_subnet.private_subnet[*].id
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

output "jenkins_server_public_dns" {
  description = "The public DNS of the Jenkins server"
  value       = aws_instance.jenkins_server.public_dns
}

output "api_server_public_ip" {
  description = "The public IP of the API server"
  value       = aws_instance.api_server.public_ip
}

output "api_server_public_dns" {
  description = "The public DNS of the API server"
  value       = aws_instance.api_server.public_dns
}

output "api_load_balancer_dns" {
  description = "The DNS name of the API load balancer"
  value       = aws_lb.api_lb.dns_name
}

output "api_endpoint" {
  description = "The endpoint URL for the API"
  value       = "http://${aws_lb.api_lb.dns_name}"
}
