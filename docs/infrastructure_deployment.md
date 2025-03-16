# Infrastructure Deployment Guide

This guide provides detailed instructions for deploying the FTTH Fiber Optic Fault Detection system infrastructure on AWS using Terraform and Ansible.

## Prerequisites

Before you begin, ensure you have the following:

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Terraform (v1.0.0+) installed
- Ansible (v2.9+) installed
- SSH key pair for EC2 instance access

## Step 1: Configure AWS Credentials

Set up your AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

Alternatively, configure the AWS CLI:

```bash
aws configure
```

## Step 2: Prepare Terraform Variables

1. Navigate to the Terraform directory:

```bash
cd infrastructure/terraform
```

2. Create a `terraform.tfvars` file with your specific values:

```hcl
aws_region = "us-east-1"
environment = "dev"
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
s3_bucket_prefix = "ftth-fault-detection"
ecr_repository_name = "ftth-fault-detection"
jenkins_instance_type = "t3.medium"
api_instance_type = "t3.medium"
training_instance_type = "g4dn.xlarge"
key_name = "your-key-pair-name"
```

## Step 3: Initialize and Apply Terraform

1. Initialize Terraform:

```bash
terraform init
```

2. Create an execution plan:

```bash
terraform plan -out=tfplan
```

3. Review the plan and apply:

```bash
terraform apply tfplan
```

4. After successful deployment, note the outputs:

```bash
terraform output
```

Save the following values for use with Ansible:
- VPC ID
- S3 bucket name
- ECR repository URL
- Jenkins server public IP
- API server public IP
- Load balancer DNS name

## Step 4: Prepare Ansible Inventory

1. Navigate to the Ansible directory:

```bash
cd ../ansible
```

2. Update the `inventory.ini` file with the EC2 instance IPs from Terraform output:

```ini
[jenkins]
jenkins_server ansible_host=<jenkins_server_public_ip> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/your-key.pem

[api_server]
api_server ansible_host=<api_server_public_ip> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/your-key.pem

[staging]
api_server ansible_host=<api_server_public_ip> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/your-key.pem

[production]
# Add production server when ready

[all:vars]
ansible_python_interpreter=/usr/bin/python3
aws_region=us-east-1
aws_access_key={{ lookup('env', 'AWS_ACCESS_KEY_ID') }}
aws_secret_key={{ lookup('env', 'AWS_SECRET_ACCESS_KEY') }}
ecr_repository_url=<ecr_repository_url>
s3_bucket_name=<s3_bucket_name>
```

## Step 5: Update Ansible Variables

1. Update the `vars/main.yml` file with your specific values:

```yaml
# AWS Configuration
aws_region: "us-east-1"
s3_bucket_name: "<s3_bucket_name>"
ecr_repository_url: "<ecr_repository_url>"

# Docker Configuration
docker_compose_version: "1.29.2"

# API Configuration
api_port: 8000
api_container_name: "ftth-api"
api_image_tag: "latest"
api_log_level: "info"

# Jenkins Configuration
jenkins_http_port: 8080
jenkins_home: "/var/lib/jenkins"
jenkins_admin_username: "admin"
jenkins_admin_password: "changeme"  # Change this!

# Training Configuration
training_data_dir: "/opt/ftth/data"
training_model_dir: "/opt/ftth/models"
training_log_dir: "/opt/ftth/logs"

# Common paths
app_base_dir: "/opt/ftth"
log_dir: "/var/log/ftth"
```

## Step 6: Run Ansible Playbooks

1. Run the Ansible playbook:

```bash
ansible-playbook -i inventory.ini site.yml
```

This will configure all servers according to their roles.

2. To deploy only specific components, use tags or limit to specific hosts:

```bash
# Deploy only Jenkins
ansible-playbook -i inventory.ini site.yml --limit jenkins

# Deploy only API server
ansible-playbook -i inventory.ini site.yml --limit api_server
```

## Step 7: Upload Initial Data and Model

1. Upload the OTDR dataset to S3:

```bash
aws s3 cp data/OTDR_data.csv s3://<s3_bucket_name>/data/OTDR_data.csv
```

2. If you have a pre-trained model, upload it to S3:

```bash
aws s3 cp models/best_model.pkl s3://<s3_bucket_name>/models/best_model.pkl
aws s3 cp models/best_model.h5 s3://<s3_bucket_name>/models/best_model.h5
```

## Step 8: Configure Jenkins

1. Access the Jenkins server using the URL from Terraform output:

```
http://<jenkins_server_public_ip>:8080
```

2. Get the initial admin password:

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@<jenkins_server_public_ip> "sudo cat /var/lib/jenkins/secrets/initialAdminPassword"
```

3. Complete the Jenkins setup wizard and install recommended plugins.

4. Create a new pipeline job:
   - Go to "New Item"
   - Enter "ftth-fault-detection" as the name
   - Select "Pipeline" and click "OK"
   - In the configuration page, select "Pipeline script from SCM"
   - Set SCM to Git and enter your repository URL
   - Set the script path to "Jenkinsfile"
   - Save the configuration

5. Alternatively, use the provided script to set up the Jenkins job:

```bash
cd ../../ci_cd
chmod +x setup_jenkins_job.sh
./setup_jenkins_job.sh
```

## Step 9: Verify Deployment

1. Check the API health endpoint:

```bash
curl http://<api_server_public_ip>:8000/health
```

2. Access the API documentation:

```
http://<api_server_public_ip>:8000/docs
```

3. Test a prediction:

```bash
curl -X POST "http://<api_server_public_ip>:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
           "snr": 15.0,
           "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                           0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                           0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
         }'
```

## Troubleshooting

### Common Issues

1. **Terraform Apply Fails**:
   - Check AWS credentials and permissions
   - Verify that the specified AWS region supports all required services
   - Check for resource name conflicts

2. **Ansible Playbook Fails**:
   - Verify SSH connectivity to EC2 instances
   - Check that the correct SSH key is specified
   - Ensure Python is installed on target instances

3. **Jenkins Pipeline Fails**:
   - Check Jenkins logs for specific error messages
   - Verify AWS credentials are properly configured in Jenkins
   - Ensure all required plugins are installed

4. **API Deployment Issues**:
   - Check Docker logs: `docker logs ftth-api`
   - Verify model files are correctly uploaded to S3
   - Check API server security group allows traffic on port 8000

### Logs and Debugging

- Jenkins logs: `/var/log/jenkins/jenkins.log`
- API logs: `/var/log/ftth/api.log`
- Docker logs: `docker logs ftth-api`
- Nginx logs: `/var/log/nginx/ftth-api-access.log` and `/var/log/nginx/ftth-api-error.log`

## Cleanup

To destroy the infrastructure when no longer needed:

```bash
cd infrastructure/terraform
terraform destroy
```

Confirm the destruction when prompted.

## Security Considerations

- The default configuration exposes Jenkins and API ports publicly. For production, restrict access using security groups.
- Use AWS Secrets Manager or Parameter Store for sensitive information instead of hardcoding in files.
- Enable HTTPS for all public endpoints in production.
- Implement proper authentication for the API in production environments.
