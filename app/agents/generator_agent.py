import json
import logging
import math
from typing import Dict, Any, List
from app.models.schemas import GenerationState, GenerationBatch, ResearchResult
from app.services.llm_service import LLMService
from app.config import BATCH_SIZE

logger = logging.getLogger(__name__)

class GeneratorAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.batch_size = BATCH_SIZE
    
    async def generate_data_batch(self, state: GenerationState) -> GenerationState:
        """Generate a batch of synthetic data"""
        try:
            # Calculate remaining records needed
            records_generated = len(state.generated_data)
            records_remaining = state.num_records - records_generated
            
            if records_remaining <= 0:
                state.status = "generation_completed"
                return state
            
            # Determine batch size for this iteration
            current_batch_size = min(self.batch_size, records_remaining)
            
            logger.info(f"Generating batch {state.current_batch + 1}/{state.total_batches} "
                       f"({current_batch_size} records)")
            
            # Parse research data
            research_data = {}
            if state.domain_research:
                try:
                    research_data = json.loads(state.domain_research)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse research data, using fallback")
                    research_data = {"domain_info": state.domain_research}
            
            # Generate synthetic data using LLM
            batch_data = await self.llm_service.generate_synthetic_data(
                domain=state.domain,
                data_format=state.data_format,
                batch_size=current_batch_size,
                domain_research=research_data,
                context=state.context
            )
            
            if not batch_data:
                logger.warning(f"No data generated for batch {state.current_batch + 1}")
                state.status = "generation_failed"
                state.error_message = "Failed to generate data batch"
                return state
            
            # Add batch to generated data
            state.generated_data.extend(batch_data)
            state.current_batch += 1
            
            # Update status
            if len(state.generated_data) >= state.num_records:
                state.status = "generation_completed"
                logger.info(f"Data generation completed: {len(state.generated_data)} records")
            else:
                state.status = "generating"
                logger.info(f"Progress: {len(state.generated_data)}/{state.num_records} records")
            
            return state
            
        except Exception as e:
            logger.error(f"Data generation failed: {str(e)}")
            state.status = "generation_failed"
            state.error_message = f"Generation failed: {str(e)}"
            return state
    
    def calculate_batches(self, total_records: int, batch_size: int = None) -> int:
        """Calculate number of batches needed"""
        if batch_size is None:
            batch_size = self.batch_size
        return math.ceil(total_records / batch_size)
    
    def should_continue_generation(self, state: GenerationState) -> bool:
        """Check if generation should continue"""
        return (len(state.generated_data) < state.num_records and 
                state.status not in ["generation_failed", "generation_completed"])
    
    async def __call__(self, state: GenerationState) -> GenerationState:
        """Main entry point for the generator agent"""
        # Initialize batch tracking on first call
        if state.total_batches == 0:
            state.total_batches = self.calculate_batches(state.num_records)
            state.current_batch = 0
            logger.info(f"Initialized generation: {state.total_batches} batches needed")
        
        return await self.generate_data_batch(state)