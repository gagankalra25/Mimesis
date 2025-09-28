import logging
from typing import Dict, Any, List, Set
from app.models.schemas import GenerationState, EvaluationResult
from app.services.llm_service import LLMService
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.file_service = FileService()
    
    def remove_exact_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove exact duplicate records"""
        seen = set()
        unique_data = []
        
        for record in data:
            # Create a hashable representation of the record
            record_str = str(sorted(record.items()))
            if record_str not in seen:
                seen.add(record_str)
                unique_data.append(record)
        
        return unique_data
    
    def basic_quality_check(self, data: List[Dict[str, Any]], data_format: str) -> List[Dict[str, Any]]:
        """Perform basic quality checks on the data"""
        valid_records = []
        
        for record in data:
            is_valid = True
            
            # Check for empty or very short values
            for key, value in record.items():
                if isinstance(value, str):
                    if len(value.strip()) < 3:
                        is_valid = False
                        break
                    # Check for placeholder text
                    if value.lower() in ['placeholder', 'example', 'sample', 'test', '...']:
                        is_valid = False
                        break
                elif isinstance(value, dict):
                    # For metadata fields, ensure it's not empty
                    if not value:
                        is_valid = False
                        break
            
            if is_valid:
                valid_records.append(record)
        
        return valid_records
    
    async def evaluate_with_llm(self, data: List[Dict[str, Any]], data_format: str) -> EvaluationResult:
        """Use LLM to evaluate data quality"""
        try:
            evaluation_result = await self.llm_service.evaluate_data_quality(data, data_format)
            
            return EvaluationResult(
                valid_records=evaluation_result.get("valid_records", data),
                duplicate_count=evaluation_result.get("duplicate_count", 0),
                quality_issues=evaluation_result.get("quality_issues", []),
                passed_validation=evaluation_result.get("passed_validation", True)
            )
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed, using basic validation: {str(e)}")
            
            # Fallback to basic validation
            unique_data = self.remove_exact_duplicates(data)
            valid_data = self.basic_quality_check(unique_data, data_format)
            
            return EvaluationResult(
                valid_records=valid_data,
                duplicate_count=len(data) - len(unique_data),
                quality_issues=["Basic validation only - LLM evaluation failed"],
                passed_validation=len(valid_data) > 0
            )
    
    async def evaluate_and_save(self, state: GenerationState) -> GenerationState:
        """Evaluate data quality and save to file"""
        try:
            logger.info(f"Evaluating {len(state.generated_data)} generated records")
            
            # First pass: Remove exact duplicates and basic quality check
            unique_data = self.remove_exact_duplicates(state.generated_data)
            basic_valid_data = self.basic_quality_check(unique_data, state.data_format)
            
            logger.info(f"After basic validation: {len(basic_valid_data)} records remain")
            
            # Second pass: LLM-based evaluation for final quality check
            evaluation_result = await self.evaluate_with_llm(basic_valid_data, state.data_format)
            
            final_data = evaluation_result.valid_records
            logger.info(f"After LLM evaluation: {len(final_data)} valid records")
            
            if not final_data:
                state.status = "evaluation_failed"
                state.error_message = "No valid records after evaluation"
                return state
            
            # Validate data format before saving
            if not self.file_service.validate_data_format(final_data, state.data_format):
                logger.warning("Data format validation failed, but proceeding with save")
            
            # Save to CSV file
            file_path = self.file_service.save_to_csv(final_data, state.domain, state.data_format)
            
            # Update state with results
            state.generated_data = final_data  # Update with validated data
            state.file_path = file_path
            state.status = "completed"
            
            logger.info(f"Evaluation completed: {len(final_data)} records saved to {file_path}")
            return state
            
        except Exception as e:
            logger.error(f"Evaluation and save failed: {str(e)}")
            state.status = "evaluation_failed"
            state.error_message = f"Evaluation failed: {str(e)}"
            return state
    
    def get_quality_metrics(self, original_count: int, final_count: int, 
                           duplicate_count: int, quality_issues: List[str]) -> Dict[str, Any]:
        """Generate quality metrics for the evaluation"""
        return {
            "original_records": original_count,
            "final_records": final_count,
            "duplicates_removed": duplicate_count,
            "quality_issues": quality_issues,
            "success_rate": final_count / original_count if original_count > 0 else 0,
            "quality_score": max(0, 1 - (len(quality_issues) / 10))  # Simple quality score
        }
    
    async def __call__(self, state: GenerationState) -> GenerationState:
        """Main entry point for the evaluator agent"""
        return await self.evaluate_and_save(state)