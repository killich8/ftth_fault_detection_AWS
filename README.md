# FTTH Fiber Optic Fault Detection

This project aims to automatically detect faults in FTTH fiber optic cables by analyzing OTDR traces using an AI model. The entire infrastructure and deployment is automated on AWS using Terraform, Ansible, and Jenkins.

## Project Overview

Fiber To The Home (FTTH) networks require constant monitoring to ensure service quality. Optical Time Domain Reflectometer (OTDR) traces provide valuable information about the state of fiber optic cables, but analyzing these traces manually is time-consuming and error-prone. This project implements an AI-based solution to automatically detect various types of faults in fiber optic cables from OTDR trace data.

## Project Objectives

- Develop an AI model to analyze OTDR traces and detect anomalies (fiber cuts, dirty connectors, faulty splices, etc.)
- Deploy a FastAPI-based API that receives OTDR data and returns real-time predictions
- Leverage AWS for training, data storage, and API hosting
- Automate infrastructure deployment with Terraform and Ansible to provision AWS services
- Implement a CI/CD pipeline with Jenkins to manage model training, containerization, and deployment on AWS

## Fault Types

The model is trained to detect the following types of optical fiber events:
- 0: Normal (no fault)
- 1: Fiber tapping
- 2: Bad splice
- 3: Bending event
- 4: Dirty connector
- 5: Fiber cut
- 6: PC connector
- 7: Reflector

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

## Getting Started

See the documentation in the `docs/` directory for detailed instructions on setting up and using this project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
