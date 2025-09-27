import json
import logging
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from config import GROQ_API_KEY, GROQ_MODELS, MAX_RETRIES

logger = logging.getLogger(__name__)

# Structured output models
class DomainResearchResult(BaseModel):
    """Structured model for domain research results"""
    domain_info: str = Field(description="Comprehensive domain overview")
    key_concepts: List[str] = Field(description="List of key domain concepts")
    terminology: List[str] = Field(description="Domain-specific terminology")
    context_enriched: str = Field(description="Enhanced context for data generation")

class QnARecord(BaseModel):
    """Q&A record structure"""
    question: str = Field(description="Question text", min_length=10)
    answer: str = Field(description="Answer text", min_length=10)
    context: str = Field(description="Context information", min_length=5)

class EntityRelationshipRecord(BaseModel):
    """Entity relationship record structure"""
    entity1: str = Field(description="First entity", min_length=2)
    relationship: str = Field(description="Relationship type", min_length=3)
    entity2: str = Field(description="Second entity", min_length=2)

class RagChunkRecord(BaseModel):
    """RAG chunk record structure"""
    content: str = Field(description="Main content", min_length=50)
    metadata: Dict[str, Any] = Field(description="Metadata dictionary")
    summary: str = Field(description="Content summary", min_length=10)

class FineTuningRecord(BaseModel):
    """Fine-tuning record structure"""
    instruction: str = Field(description="Instruction text", min_length=10)
    input: str = Field(description="Input text", min_length=5)
    output: str = Field(description="Expected output", min_length=5)

class SyntheticDataBatch(BaseModel):
    """Batch of synthetic data records"""
    records: List[Dict[str, Any]] = Field(description="List of generated records")

class DataEvaluation(BaseModel):
    """Data quality evaluation result"""
    valid_records: List[Dict[str, Any]] = Field(description="Records that passed validation")
    duplicate_count: int = Field(description="Number of duplicates found")
    quality_issues: List[str] = Field(description="List of quality issues")
    passed_validation: bool = Field(description="Whether validation passed")

class LLMService:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=GROQ_MODELS["default"],
            temperature=0.7,
            max_tokens=4000,
            max_retries=MAX_RETRIES
        )
    
    async def research_domain(self, domain: str, domain_context: str) -> Dict[str, Any]:
        """Research domain using structured output with React prompting"""
        
        # Create structured LLM
        structured_llm = self.llm.with_structured_output(DomainResearchResult)
        
        system_message = SystemMessage(content="""You are a domain research expert. Use the React prompting framework to thoroughly research the given domain.

React Framework:
- Thought: Analyze what you need to research about this domain
- Action: Identify key areas to investigate
- Observation: Gather insights about the domain
- Reflection: Synthesize findings into structured knowledge

Provide comprehensive domain research including terminology, concepts, and context.""")

        human_message = HumanMessage(content=f"""
Domain: {domain}
Context: {domain_context}

Using React prompting, research this domain thoroughly:

Thought: I need to understand the core aspects of {domain} domain including key terminology, common concepts, typical scenarios, and relevant contexts.

Action: Research the following areas:
1. Key terminology and jargon specific to {domain}
2. Common processes, procedures, or workflows
3. Typical challenges and problem areas
4. Industry standards and best practices
5. Current trends and developments

Observation: [Conduct thorough analysis of the domain]

Reflection: [Synthesize findings into actionable knowledge]

Provide structured output with:
- domain_info: comprehensive domain overview
- key_concepts: list of key concepts
- terminology: list of domain-specific terms
- context_enriched: enhanced context for data generation
""")
        
        try:
            result = await structured_llm.ainvoke([system_message, human_message])
            return result.model_dump()
        except Exception as e:
            logger.error(f"Domain research failed: {str(e)}")
            return {
                "domain_info": domain_context,
                "key_concepts": [],
                "terminology": [],
                "context_enriched": domain_context
            }
    
    def _get_record_model(self, data_format: str):
        """Get the appropriate Pydantic model for data format"""
        format_models = {
            "qna": QnARecord,
            "entity_relationships": EntityRelationshipRecord,
            "rag_chunks": RagChunkRecord,
            "fine_tuning": FineTuningRecord
        }
        return format_models.get(data_format, QnARecord)
    
    async def generate_synthetic_data(self, domain: str, data_format: str, batch_size: int, 
                                    domain_research: Dict[str, Any], context: str = None) -> List[Dict[str, Any]]:
        """Generate synthetic data using structured output with React prompting"""
        
        # Get the record model for this format
        record_model = self._get_record_model(data_format)
        
        # Create a dynamic list model for the batch
        class DataBatch(BaseModel):
            records: List[record_model] = Field(description=f"List of {batch_size} {data_format} records")
        
        structured_llm = self.llm.with_structured_output(DataBatch)
        
        format_descriptions = {
            "qna": "Generate question-answer pairs with context for educational or training purposes",
            "entity_relationships": "Generate entity relationships showing connections between domain concepts",
            "rag_chunks": "Generate content chunks optimized for retrieval augmented generation",
            "fine_tuning": "Generate instruction-input-output triplets for model training"
        }
        
        system_message = SystemMessage(content=f"""You are a synthetic data generation expert specializing in {domain}. 
Use React prompting to create high-quality, realistic synthetic data in {data_format} format.

React Framework:
- Thought: Plan the data generation strategy
- Action: Create diverse, realistic records
- Observation: Review generated data for quality
- Reflection: Ensure data meets requirements

{format_descriptions.get(data_format, "")}

Generate exactly {batch_size} unique, high-quality records.""")

        human_message = HumanMessage(content=f"""
Domain: {domain}
Format: {data_format}
Records needed: {batch_size}
Context: {context or "General domain knowledge"}

Domain Research:
{json.dumps(domain_research, indent=2)}

Using React prompting, generate {batch_size} diverse synthetic data records:

Thought: I need to create {batch_size} unique, realistic {data_format} records for the {domain} domain. 
The data should be diverse, high-quality, and reflect real-world scenarios in this domain.

Action: Generate records that:
- Use domain-specific terminology from the research
- Reflect realistic scenarios and use cases
- Vary in complexity and scope
- Are factually consistent and logical
- Follow the exact schema requirements

Observation: Each record should be unique, well-structured, and domain-appropriate.

Reflection: Ensure all records are distinct, high-quality, and properly formatted.

Generate exactly {batch_size} records in the specified format.
""")
        
        try:
            result = await structured_llm.ainvoke([system_message, human_message])
            # Convert Pydantic models to dicts
            return [record.model_dump() for record in result.records]
        except Exception as e:
            logger.error(f"Data generation failed: {str(e)}")
            return []
    
    async def evaluate_data_quality(self, data: List[Dict[str, Any]], data_format: str) -> Dict[str, Any]:
        """Evaluate data quality using structured output with React prompting"""
        
        structured_llm = self.llm.with_structured_output(DataEvaluation)
        
        system_message = SystemMessage(content="""You are a data quality expert. Use React prompting to evaluate synthetic data quality, 
identify duplicates, and filter out low-quality records.""")

        human_message = HumanMessage(content=f"""
Data Format: {data_format}
Records to evaluate: {len(data)}

Data:
{json.dumps(data, indent=2)}

Using React prompting, evaluate this synthetic data:

Thought: I need to assess data quality by checking for duplicates, identifying low-quality records, 
and ensuring format compliance.

Action: Evaluate each record for:
1. Uniqueness (no exact or near-duplicates)
2. Quality (realistic, coherent, well-structured)
3. Format compliance (correct fields and data types)
4. Content appropriateness (relevant to domain)

Observation: Identify which records pass quality checks and which should be filtered out.

Reflection: Provide final assessment with valid records only.

Return evaluation results with valid records, duplicate count, and quality assessment.
""")
        
        try:
            result = await structured_llm.ainvoke([system_message, human_message])
            return result.model_dump()
        except Exception as e:
            logger.warning(f"LLM evaluation failed, using basic validation: {str(e)}")
            
            # Fallback to basic validation
            return {
                "valid_records": data,
                "duplicate_count": 0,
                "quality_issues": ["LLM evaluation failed - using basic validation"],
                "passed_validation": len(data) > 0
            }