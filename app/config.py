import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
MAX_RECORDS_PER_REQUEST = int(os.getenv("MAX_RECORDS_PER_REQUEST", "1000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# File Configuration
RESPONSES_DIR = "responses"
if not os.path.exists(RESPONSES_DIR):
    os.makedirs(RESPONSES_DIR)

# Supported Domains
SUPPORTED_DOMAINS = {
    "healthcare": {
        "description": "Medical, pharmaceutical, clinical research, patient care, diagnostics",
        "keywords": ["medical", "patient", "diagnosis", "treatment", "healthcare", "clinical"]
    },
    "finance": {
        "description": "Banking, investments, trading, financial planning, risk management",
        "keywords": ["banking", "investment", "finance", "trading", "risk", "financial"]
    },
    "business": {
        "description": "Management, operations, strategy, marketing, entrepreneurship",
        "keywords": ["business", "strategy", "management", "operations", "marketing"]
    },
    "law": {
        "description": "Legal procedures, contracts, regulations, compliance, litigation",
        "keywords": ["legal", "law", "contract", "regulation", "compliance", "court"]
    },
    "technology": {
        "description": "Software development, AI/ML, cybersecurity, cloud computing",
        "keywords": ["technology", "software", "AI", "cybersecurity", "cloud", "development"]
    },
    "education": {
        "description": "Learning, curriculum, pedagogy, assessment, educational technology",
        "keywords": ["education", "learning", "curriculum", "teaching", "assessment"]
    }
}

# Supported Data Formats
SUPPORTED_FORMATS = {
    "qna": {
        "description": "Question and Answer pairs with context",
        "fields": ["question", "answer", "context"]
    },
    "entity_relationships": {
        "description": "Entity relationship mappings",
        "fields": ["entity1", "relationship", "entity2"]
    },
    "rag_chunks": {
        "description": "RAG-optimized content chunks with metadata",
        "fields": ["content", "metadata", "summary"]
    },
    "fine_tuning": {
        "description": "Instruction-input-output format for model training",
        "fields": ["instruction", "input", "output"]
    }
}

# LLM Configuration
GROQ_MODELS = {
    "default": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "fast": "llama-3.1-8b-instant",
    "advanced": "mixtral-8x7b-32768"
}