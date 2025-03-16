from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import routers
from api.admin import router as admin_router
from api.validation import router as validation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/api.log")
    ]
)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="FTTH Fiber Optic Fault Detection API",
    description="API for detecting faults in FTTH fiber optic cables using OTDR traces",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router)
app.include_router(validation_router)

# Import main router after to avoid circular imports
from api.main import router as main_router
app.include_router(main_router)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "FTTH Fiber Optic Fault Detection API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
