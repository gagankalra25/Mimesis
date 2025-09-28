import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models.schemas import SyntheticDataRequest, SyntheticDataResponse, StatusEnum
from app.agents.langgraph_workflow import SyntheticDataWorkflow
from app.utils.helpers import validate_request_data, format_duration, timing_decorator
from app.config import ENVIRONMENT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global workflow instance
workflow_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global workflow_instance
    
    # Startup
    logger.info("Starting Synthetic Data Generator API")
    workflow_instance = SyntheticDataWorkflow()
    logger.info("LangGraph workflow initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Synthetic Data Generator API")

# Initialize FastAPI app
app = FastAPI(
    title="Synthetic Data Generator",
    description="LangGraph-powered synthetic data generation API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Synthetic Data Generator API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT
    }

@app.get("/supported-domains")
async def get_supported_domains():
    """Get list of supported domains"""
    from config import SUPPORTED_DOMAINS
    return {
        "domains": list(SUPPORTED_DOMAINS.keys()),
        "details": SUPPORTED_DOMAINS
    }

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported data formats"""
    from config import SUPPORTED_FORMATS
    return {
        "formats": list(SUPPORTED_FORMATS.keys()),
        "details": SUPPORTED_FORMATS
    }

@timing_decorator
async def process_data_generation(request: SyntheticDataRequest) -> SyntheticDataResponse:
    """Process synthetic data generation request"""
    start_time = time.time()
    
    try:
        # Run the workflow
        final_state = await workflow_instance.run_workflow(
            domain=request.domain.value,
            data_format=request.data_format.value,
            num_records=request.num_records,
            context=request.context
        )
        
        end_time = time.time()
        generation_time = format_duration(end_time - start_time)
        
        if final_state.status == "completed":
            return SyntheticDataResponse(
                status=StatusEnum.COMPLETED,
                total_records=len(final_state.generated_data),
                file_path=final_state.file_path or "unknown",
                generation_time=generation_time,
                message="Data generation completed successfully"
            )
        else:
            error_msg = final_state.error_message or "Unknown error occurred"
            return SyntheticDataResponse(
                status=StatusEnum.FAILED,
                total_records=len(final_state.generated_data),
                file_path="",
                generation_time=generation_time,
                message=f"Data generation failed: {error_msg}"
            )
    
    except Exception as e:
        end_time = time.time()
        generation_time = format_duration(end_time - start_time)
        logger.error(f"Data generation failed: {str(e)}")
        
        return SyntheticDataResponse(
            status=StatusEnum.FAILED,
            total_records=0,
            file_path="",
            generation_time=generation_time,
            message=f"Generation failed: {str(e)}"
        )

@app.post("/generate-synthetic-data", response_model=SyntheticDataResponse)
async def generate_synthetic_data(request: SyntheticDataRequest):
    """
    Generate synthetic data based on domain and format specifications.
    
    - **domain**: Target domain for data generation (healthcare, finance, business, law, technology, education)
    - **data_format**: Format of synthetic data (qna, entity_relationships, rag_chunks, fine_tuning)  
    - **num_records**: Number of records to generate (1-1000)
    - **context**: Optional additional context for specialization
    """
    
    # Validate request parameters
    validation_errors = validate_request_data(
        request.domain.value, 
        request.data_format.value, 
        request.num_records
    )
    
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid request parameters",
                "errors": validation_errors
            }
        )
    
    logger.info(f"Processing request: {request.domain.value} - {request.data_format.value} - {request.num_records} records")
    
    try:
        # Process the request
        response = await process_data_generation(request)
        
        if response.status == StatusEnum.FAILED:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": response.message,
                    "generation_time": response.generation_time
                }
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Internal server error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/files/{file_path:path}")
async def get_file_info(file_path: str):
    """Get information about a generated file"""
    from services.file_service import FileService
    
    file_service = FileService()
    file_stats = file_service.get_file_stats(file_path)
    
    if not file_stats.get("exists", False):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    return file_stats


@app.get("/file-sample")
async def get_file_sample_simple(file_path: str, num_rows: int = 5):
    """Get a sample of records from a generated file using query parameter"""
    from services.file_service import FileService
    
    # Ensure the file path is relative to responses directory
    if not file_path.startswith('responses/'):
        file_path = f"responses/{file_path}"
    
    file_service = FileService()
    
    # Check if file exists
    file_stats = file_service.get_file_stats(file_path)
    if not file_stats.get("exists", False):
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}"
        )
    
    # Validate num_rows
    if num_rows < 1 or num_rows > 100:
        raise HTTPException(
            status_code=400,
            detail="num_rows must be between 1 and 100"
        )
    
    try:
        sample_data = file_service.read_csv_sample(file_path, num_rows)
        
        return {
            "file_path": file_path,
            "sample_rows": len(sample_data),
            "total_records": file_stats.get("record_count", 0),
            "data": sample_data
        }
        
    except Exception as e:
        logger.error(f"Failed to read file sample: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file sample: {str(e)}"
        )


@app.delete("/cleanup")
async def cleanup_old_files(days_old: int = 7):
    """Clean up files older than specified days"""
    from services.file_service import FileService
    
    if days_old < 1:
        raise HTTPException(
            status_code=400,
            detail="days_old must be at least 1"
        )
    
    file_service = FileService()
    cleaned_count = file_service.cleanup_old_files(days_old)
    
    return {
        "message": f"Cleaned up {cleaned_count} files older than {days_old} days",
        "files_removed": cleaned_count,
        "timestamp": datetime.now().isoformat()
    }

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "development"
    )