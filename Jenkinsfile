pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REPOSITORY = 'ftth-fault-detection'
        S3_BUCKET = 'ftth-fault-detection-data'
        MODEL_PATH = 's3://ftth-fault-detection-data/models/best_model.pkl'
        DOCKER_IMAGE = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${BUILD_NUMBER}"
        DOCKER_IMAGE_LATEST = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/
                '''
            }
        }
        
        stage('Train Model') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/model/train.py
                '''
            }
        }
        
        stage('Evaluate Model') {
            steps {
                sh '''
                    . venv/bin/activate
                    python3 src/model/evaluate.py
                '''
            }
        }
        
        stage('Upload Model to S3') {
            steps {
                sh '''
                    . venv/bin/activate
                    aws s3 cp models/best_model.pkl s3://${S3_BUCKET}/models/best_model.pkl
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${DOCKER_IMAGE} .
                    docker tag ${DOCKER_IMAGE} ${DOCKER_IMAGE_LATEST}
                '''
            }
        }
        
        stage('Push to ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
                    docker push ${DOCKER_IMAGE}
                    docker push ${DOCKER_IMAGE_LATEST}
                '''
            }
        }
        
        stage('Deploy to API Server') {
            steps {
                sh '''
                    cd infrastructure/ansible
                    ansible-playbook -i inventory.ini api_setup.yml -e "aws_region=${AWS_REGION} ecr_repository_url=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY} s3_bucket_name=${S3_BUCKET}"
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
