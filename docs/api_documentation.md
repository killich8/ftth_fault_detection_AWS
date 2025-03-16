# API Documentation

## Overview

The FTTH Fiber Optic Fault Detection API provides endpoints for detecting faults in fiber optic cables using OTDR traces. The API is built with FastAPI and provides automatic Swagger documentation.

## Base URL

```
http://<api-endpoint>:8000
```

Replace `<api-endpoint>` with the actual API server address or load balancer DNS.

## Authentication

Currently, the API does not require authentication. For production deployments, it is recommended to implement an authentication mechanism.

## Endpoints

### Health Check

```
GET /health
```

Returns the health status of the API.

**Response**:
```json
{
  "status": "healthy"
}
```

### Fault Types

```
GET /fault-types
```

Returns information about the supported fault types.

**Response**:
```json
{
  "fault_types": [
    {"code": 0, "name": "Normal", "description": "No fault detected"},
    {"code": 1, "name": "Fiber Tapping", "description": "Unauthorized access to the fiber"},
    {"code": 2, "name": "Bad Splice", "description": "Poor quality fiber splice"},
    {"code": 3, "name": "Bending Event", "description": "Excessive bending of the fiber"},
    {"code": 4, "name": "Dirty Connector", "description": "Contaminated fiber connector"},
    {"code": 5, "name": "Fiber Cut", "description": "Complete break in the fiber"},
    {"code": 6, "name": "PC Connector", "description": "Physical Contact connector"},
    {"code": 7, "name": "Reflector", "description": "Reflective event in the fiber"}
  ]
}
```

### Single Prediction

```
POST /predict
```

Predicts the fault type from a single OTDR trace.

**Request Body**:
```json
{
  "snr": 15.0,
  "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                  0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                  0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
}
```

**Parameters**:
- `snr` (float, required): Signal-to-noise ratio
- `trace_points` (array of 30 floats, required): Normalized OTDR trace points [P1...P30]

**Response**:
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

### Batch Prediction

```
POST /batch-predict
```

Predicts fault types from multiple OTDR traces.

**Request Body**:
```json
{
  "traces": [
    {
      "snr": 15.0,
      "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                      0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                      0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
    },
    {
      "snr": 12.5,
      "trace_points": [0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2,
                      0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8,
                      0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2]
    }
  ]
}
```

**Response**:
```json
{
  "predictions": [
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
    },
    {
      "fault_type": 4,
      "fault_name": "Dirty Connector",
      "confidence": 0.88,
      "all_probabilities": {
        "Normal": 0.02,
        "Fiber Tapping": 0.03,
        "Bad Splice": 0.05,
        "Bending Event": 0.01,
        "Dirty Connector": 0.88,
        "Fiber Cut": 0.005,
        "PC Connector": 0.005,
        "Reflector": 0.01
      }
    }
  ]
}
```

### Trace Validation

```
POST /validation/trace
```

Validates OTDR trace data before prediction.

**Request Body**:
```json
{
  "snr": 15.0,
  "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                  0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                  0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
}
```

**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "stats": {
    "trace_min": 0.0,
    "trace_max": 1.0,
    "trace_mean": 0.5,
    "trace_std": 0.3,
    "trace_range": 1.0
  }
}
```

### System Information

```
GET /admin/system-info
```

Returns information about the system configuration.

**Response**:
```json
{
  "api_version": "1.0.0",
  "model_info": {
    "model_type": "lstm",
    "input_features": 31,
    "hidden_layers": [128, 64],
    "model_path": "models/best_model.pkl"
  },
  "config": {
    "data": {
      "raw_data_path": "data/OTDR_data.csv",
      "processed_data_path": "data/processed/",
      "train_test_split": 0.2,
      "validation_split": 0.1,
      "random_seed": 42
    },
    "model": {
      "model_type": "lstm",
      "input_features": 31,
      "hidden_layers": [128, 64],
      "dropout_rate": 0.3,
      "learning_rate": 0.001,
      "batch_size": 64,
      "epochs": 50,
      "early_stopping_patience": 10
    },
    "api": {
      "host": "0.0.0.0",
      "port": 8000,
      "log_level": "info"
    }
  }
}
```

### Model Status

```
GET /admin/model-status
```

Returns the status of the loaded model.

**Response**:
```json
{
  "status": "active",
  "model_type": "lstm",
  "model_path": "models/best_model.pkl",
  "class_names": ["Normal", "Fiber Tapping", "Bad Splice", "Bending Event", 
                 "Dirty Connector", "Fiber Cut", "PC Connector", "Reflector"]
}
```

## Error Handling

The API returns standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid input)
- 422: Validation Error (input fails validation)
- 500: Internal Server Error

Error responses include a detail message:

```json
{
  "detail": "Error message describing the issue"
}
```

## Swagger Documentation

The API provides automatic Swagger documentation at:

```
GET /docs
```

This interactive documentation allows you to test the API endpoints directly from your browser.

## OpenAPI Specification

The OpenAPI specification is available at:

```
GET /openapi.json
```

This can be used to generate client libraries in various programming languages.
