pipeline {
    agent any
    
    environment {
        AWS_REGION = "${params.AWS_REGION ?: 'us-east-1'}"
        S3_BUCKET = "${params.S3_BUCKET}"
        ECR_REPOSITORY = "${params.ECR_REPOSITORY}"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        DEPLOY_TO_PRODUCTION = "${params.DEPLOY_TO_PRODUCTION ?: 'false'}"
    }
    
    parameters {
        string(name: 'AWS_REGION', defaultValue: 'us-east-1', description: 'AWS Region')
        string(name: 'S3_BUCKET', description: 'S3 Bucket for storing data and models')
        string(name: 'ECR_REPOSITORY', description: 'ECR Repository URL')
        booleanParam(name: 'DEPLOY_TO_PRODUCTION', defaultValue: false, description: 'Deploy to production environment')
        booleanParam(name: 'RETRAIN_MODEL', defaultValue: false, description: 'Retrain the model with latest data')
        choice(name: 'MODEL_TYPE', choices: ['lstm', 'cnn', 'dense'], description: 'Type of model to train')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1'
                sh 'ls -la'
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    python3 -m pip install -r requirements.txt
                    mkdir -p data/processed
                    mkdir -p models
                    mkdir -p logs
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    python3 -m pytest tests/ -v
                    python3 -m pytest src/api/tests/ -v
                '''
            }
        }
        
        stage('Process Data') {
            steps {
                sh '''
                    # Download data from S3 if not exists locally
                    if [ ! -f data/OTDR_data.csv ]; then
                        aws s3 cp s3://${S3_BUCKET}/data/OTDR_data.csv data/OTDR_data.csv
                    fi
                    
                    # Run data preprocessing
                    cd src/data_processing
                    python3 preprocess.py
                '''
            }
        }
        
        stage('Train Model') {
            when {
                expression { return params.RETRAIN_MODEL == true }
            }
            steps {
                sh '''
                    # Set model type from parameters
                    sed -i "s/model_type: .*/model_type: \\"${MODEL_TYPE}\\"/g" config.yaml
                    
                    # Train the model
                    cd src/model
                    python3 train.py
                    
                    # Upload model to S3
                    aws s3 cp models/best_model.pkl s3://${S3_BUCKET}/models/best_model.pkl
                    aws s3 cp models/best_model.h5 s3://${S3_BUCKET}/models/best_model.h5
                '''
            }
        }
        
        stage('Evaluate Model') {
            steps {
                sh '''
                    # Download model from S3 if not retrained
                    if [ "${RETRAIN_MODEL}" = "false" ]; then
                        aws s3 cp s3://${S3_BUCKET}/models/best_model.pkl models/best_model.pkl
                        aws s3 cp s3://${S3_BUCKET}/models/best_model.h5 models/best_model.h5
                    fi
                    
                    # Evaluate the model
                    cd src/model
                    python3 evaluate.py
                '''
                
                // Archive evaluation results
                archiveArtifacts artifacts: 'models/*.png, models/*.txt', fingerprint: true
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                    # Login to ECR
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY}
                    
                    # Build and tag Docker image
                    docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} -f Dockerfile.api .
                    docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REPOSITORY}:latest
                '''
            }
        }
        
        stage('Push Docker Image') {
            steps {
                sh '''
                    # Push Docker image to ECR
                    docker push ${ECR_REPOSITORY}:${IMAGE_TAG}
                    docker push ${ECR_REPOSITORY}:latest
                '''
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                sh '''
                    # Update inventory with staging server
                    cd infrastructure/ansible
                    
                    # Run Ansible playbook for deployment
                    ansible-playbook -i inventory.ini api_setup.yml -e "ecr_repository_url=${ECR_REPOSITORY} api_image_tag=${IMAGE_TAG} s3_bucket_name=${S3_BUCKET} aws_region=${AWS_REGION}" --limit staging
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    # Run integration tests against staging environment
                    cd tests
                    python3 -m pytest integration_tests/ -v
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                expression { return params.DEPLOY_TO_PRODUCTION == true }
            }
            steps {
                // Require manual confirmation for production deployment
                input message: 'Deploy to production?', ok: 'Deploy'
                
                sh '''
                    # Update inventory with production server
                    cd infrastructure/ansible
                    
                    # Run Ansible playbook for deployment
                    ansible-playbook -i inventory.ini api_setup.yml -e "ecr_repository_url=${ECR_REPOSITORY} api_image_tag=${IMAGE_TAG} s3_bucket_name=${S3_BUCKET} aws_region=${AWS_REGION}" --limit production
                '''
            }
        }
        
        stage('Verify Deployment') {
            steps {
                sh '''
                    # Verify deployment by checking API health endpoint
                    DEPLOY_ENV="staging"
                    if [ "${DEPLOY_TO_PRODUCTION}" = "true" ]; then
                        DEPLOY_ENV="production"
                    fi
                    
                    # Get API endpoint from Ansible inventory
                    API_ENDPOINT=$(grep -A1 "\\[${DEPLOY_ENV}\\]" infrastructure/ansible/inventory.ini | tail -1 | awk '{print $2}' | cut -d'=' -f2)
                    
                    # Check API health
                    curl -f http://${API_ENDPOINT}:8000/health || exit 1
                    
                    echo "Deployment to ${DEPLOY_ENV} verified successfully!"
                '''
            }
        }
    }
    
    post {
        always {
            // Clean up Docker images
            sh '''
                docker rmi ${ECR_REPOSITORY}:${IMAGE_TAG} || true
                docker rmi ${ECR_REPOSITORY}:latest || true
            '''
            
            // Clean workspace
            cleanWs(cleanWhenNotBuilt: false,
                    deleteDirs: true,
                    disableDeferredWipeout: true,
                    notFailBuild: true,
                    patterns: [[pattern: 'data/processed/**', type: 'INCLUDE'],
                               [pattern: 'models/**', type: 'INCLUDE'],
                               [pattern: 'logs/**', type: 'INCLUDE']])
        }
        
        success {
            echo 'Pipeline completed successfully!'
        }
        
        failure {
            echo 'Pipeline failed!'
            
            // Send notification on failure
            mail to: 'team@example.com',
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "Something is wrong with ${env.BUILD_URL}"
        }
    }
}
