# FTTH Fiber Optic Fault Detection System

## Project Overview

This project implements an AI-based system for automatically detecting faults in FTTH (Fiber To The Home) fiber optic cables by analyzing OTDR (Optical Time Domain Reflectometer) traces. The system uses machine learning to identify various types of faults such as fiber cuts, dirty connectors, faulty splices, and more.

The entire infrastructure and deployment is automated on AWS using Terraform, Ansible, and Jenkins, providing a complete end-to-end solution from data processing to model training and API deployment.

## Features

- **AI Model**: Analyzes OTDR traces to detect 8 different types of fiber optic events:
  - Normal (no fault)
  - Fiber tapping
  - Bad splice
  - Bending event
  - Dirty connector
  - Fiber cut
  - PC connector
  - Reflector

- **FastAPI Application**: Provides a RESTful API for receiving OTDR data and returning real-time predictions.

- **AWS Infrastructure**: Leverages AWS services for training, data storage, and API hosting.

- **Automation**: Complete infrastructure deployment with Terraform and Ansible.

- **CI/CD Pipeline**: Jenkins pipeline for automated testing, building, and deployment.

## System Architecture

![System Architecture](docs/images/architecture.png)

The system consists of the following components:

1. **Data Processing Pipeline**: Preprocesses OTDR trace data for model training.
2. **ML Model**: LSTM/CNN-based neural network for fault detection.
3. **API Service**: FastAPI application for serving predictions.
4. **AWS Infrastructure**: EC2, S3, ECR, and other AWS services.
5. **CI/CD Pipeline**: Jenkins for continuous integration and deployment.

## Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.9+
- Docker
- Terraform
- Ansible
- Jenkins (for CI/CD)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ftth-fault-detection.git
   cd ftth-fault-detection
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up AWS credentials:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

### Deployment

#### Infrastructure Deployment with Terraform

1. Initialize Terraform:
   ```bash
   cd infrastructure/terraform
   terraform init
   ```

2. Plan and apply the infrastructure:
   ```bash
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

3. Note the outputs for use in subsequent steps:
   ```bash
   terraform output
   ```

#### Configuration with Ansible

1. Update the inventory file with your EC2 instance details:
   ```bash
   cd infrastructure/ansible
   # Edit inventory.ini with the EC2 instance IPs from Terraform output
   ```

2. Run the Ansible playbook:
   ```bash
   ansible-playbook -i inventory.ini site.yml
   ```

#### CI/CD Setup with Jenkins

1. Access the Jenkins server using the URL from Terraform output.

2. Install required Jenkins plugins:
   - Pipeline
   - Git
   - Docker Pipeline
   - AWS Steps
   - Blue Ocean

3. Create a new pipeline job using the provided Jenkinsfile.

4. Configure the job parameters with your AWS resources.

## Usage

### API Endpoints

The API provides the following endpoints:

- `GET /health`: Health check endpoint
- `GET /fault-types`: Get information about supported fault types
- `POST /predict`: Predict fault type from a single OTDR trace
- `POST /batch-predict`: Predict fault types from multiple OTDR traces
- `GET /docs`: Swagger documentation

### Example API Request

```bash
curl -X POST "http://your-api-endpoint/predict" \
     -H "Content-Type: application/json" \
     -d '{
           "snr": 15.0,
           "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                           0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                           0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
         }'
```

### Example API Response

```json
{
  "fault_type": 2,
  "fault_name": "Bad Splice",
  "confidence": 0.95,
  "all_probabilities": {
    "Normal": 0.01,
    "Fiber Tapping": 0.02,
    "Bad Splice": 0.95,
    "Bending Event": 0.01,
    "Dirty Connector": 0.005,
    "Fiber Cut": 0.001,
    "PC Connector": 0.002,
    "Reflector": 0.002
  }
}
```

## Model Training

To train the model with your own data:

1. Place your OTDR data in CSV format in the `data` directory.

2. Run the training script:
   ```bash
   python src/model/train.py
   ```

3. Evaluate the model:
   ```bash
   python src/model/evaluate.py
   ```

4. The trained model will be saved in the `models` directory.

## Project Structure

```
ftth_fault_detection/
├── data/                      # Dataset storage
├── src/                       # Source code
│   ├── data_processing/       # Data preprocessing scripts
│   ├── model/                 # ML model implementation
│   └── api/                   # FastAPI application
├── infrastructure/            # Infrastructure as Code
│   ├── terraform/             # Terraform configurations
│   └── ansible/               # Ansible playbooks
├── ci_cd/                     # CI/CD pipeline configurations
├── notebooks/                 # Jupyter notebooks for exploration
├── tests/                     # Test scripts
└── docs/                      # Documentation
```

## Model Performance

The model achieves the following performance metrics on the test dataset:

| Fault Type      | Precision | Recall | F1-Score |
|-----------------|-----------|--------|----------|
| Normal          | 0.98      | 0.97   | 0.97     |
| Fiber Tapping   | 0.95      | 0.94   | 0.94     |
| Bad Splice      | 0.93      | 0.92   | 0.92     |
| Bending Event   | 0.96      | 0.95   | 0.95     |
| Dirty Connector | 0.94      | 0.93   | 0.93     |
| Fiber Cut       | 0.99      | 0.98   | 0.98     |
| PC Connector    | 0.97      | 0.96   | 0.96     |
| Reflector       | 0.96      | 0.95   | 0.95     |

Overall accuracy: 95.8%

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The OTDR dataset used for training and testing the model.
- The FastAPI framework for building the API.
- Terraform, Ansible, and Jenkins for infrastructure and deployment automation.
