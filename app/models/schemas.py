from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from enum import Enum

# Enums
class DomainEnum(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    BUSINESS = "business"
    LAW = "law"
    TECHNOLOGY = "technology"
    EDUCATION = "education"

class DataFormatEnum(str, Enum):
    QNA = "qna"
    ENTITY_RELATIONSHIPS = "entity_relationships"
    RAG_CHUNKS = "rag_chunks"
    FINE_TUNING = "fine_tuning"

class StatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Request Models
class SyntheticDataRequest(BaseModel):
    domain: DomainEnum = Field(..., description="Domain for synthetic data generation")
    data_format: DataFormatEnum = Field(..., description="Format of the synthetic data")
    num_records: int = Field(..., ge=1, le=1000, description="Number of records to generate")
    context: Optional[str] = Field(None, description="Additional context for data generation")

    @validator('num_records')
    def validate_num_records(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError('num_records must be between 1 and 1000')
        return v

# Response Models
class SyntheticDataResponse(BaseModel):
    status: StatusEnum
    total_records: int
    file_path: str
    generation_time: str
    message: Optional[str] = None

# Data Format Models (for API validation)
class QnARecordAPI(BaseModel):
    question: str = Field(..., min_length=10)
    answer: str = Field(..., min_length=10)
    context: str = Field(..., min_length=5)

class EntityRelationshipRecordAPI(BaseModel):
    entity1: str = Field(..., min_length=2)
    relationship: str = Field(..., min_length=3)
    entity2: str = Field(..., min_length=2)

class RagChunkRecordAPI(BaseModel):
    content: str = Field(..., min_length=50)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    summary: str = Field(..., min_length=10)

class FineTuningRecordAPI(BaseModel):
    instruction: str = Field(..., min_length=10)
    input: str = Field(..., min_length=5)
    output: str = Field(..., min_length=5)

# LangGraph State Model
class GenerationState(BaseModel):
    domain: str
    data_format: str
    num_records: int
    context: Optional[str] = None
    domain_research: Optional[str] = None
    generated_data: List[Dict[str, Any]] = Field(default_factory=list)
    current_batch: int = 0
    total_batches: int = 0
    file_path: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None
    
    class Config:
        # Allow extra fields for LangGraph compatibility
        extra = "allow"
        
    @classmethod
    def from_dict(cls, data: dict) -> "GenerationState":
        """Create GenerationState from dictionary safely"""
        return cls(**{k: v for k, v in data.items() if k in cls.__fields__})

# Internal Models
class ResearchResult(BaseModel):
    domain_info: str
    key_concepts: List[str]
    terminology: List[str]
    context_enriched: str

class GenerationBatch(BaseModel):
    batch_number: int
    records: List[Dict[str, Any]]
    quality_score: float = 0.0

class EvaluationResult(BaseModel):
    valid_records: List[Dict[str, Any]]
    duplicate_count: int
    quality_issues: List[str]
    passed_validation: bool