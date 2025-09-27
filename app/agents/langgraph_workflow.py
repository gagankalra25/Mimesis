import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from models.schemas import GenerationState
from agents.research_agent import ResearchAgent
from agents.generator_agent import GeneratorAgent
from agents.evaluator_agent import EvaluatorAgent

logger = logging.getLogger(__name__)

class SyntheticDataWorkflow:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.generator_agent = GeneratorAgent()
        self.evaluator_agent = EvaluatorAgent()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(GenerationState)
        
        # Add nodes
        workflow.add_node("research", self.research_node)
        workflow.add_node("generate", self.generate_node)
        workflow.add_node("evaluate", self.evaluate_node)
        
        # Add edges
        workflow.add_edge("research", "generate")
        workflow.add_edge("generate", "evaluate")
        
        # Add conditional edges for generation loop
        workflow.add_conditional_edges(
            "evaluate",
            self.should_continue_generation,
            {
                "continue": "generate",
                "end": END
            }
        )
        
        # Set entry point
        workflow.set_entry_point("research")
        
        return workflow.compile()
    
    async def research_node(self, state: GenerationState) -> GenerationState:
        """Research node wrapper"""
        logger.info("Executing research node")
        
        # Convert dict to GenerationState if needed
        if isinstance(state, dict):
            state = GenerationState(**state)
            
        result = await self.research_agent(state)
        return result
    
    async def generate_node(self, state: GenerationState) -> GenerationState:
        """Generate node wrapper"""
        # Convert dict to GenerationState if needed
        if isinstance(state, dict):
            state = GenerationState(**state)
            
        logger.info(f"Executing generation node (batch {state.current_batch + 1})")
        result = await self.generator_agent(state)
        return result
    
    async def evaluate_node(self, state: GenerationState) -> GenerationState:
        """Evaluate node wrapper"""
        logger.info("Executing evaluation node")
        
        # Convert dict to GenerationState if needed
        if isinstance(state, dict):
            state = GenerationState(**state)
        
        # Only run full evaluation if generation is complete
        if len(state.generated_data) >= state.num_records or state.status == "generation_completed":
            result = await self.evaluator_agent(state)
            return result
        else:
            # Just continue generation without full evaluation
            state.status = "generating"
            return state.model_dump()
    
    def should_continue_generation(self, state) -> str:
        """Determine if generation should continue"""
        # Convert dict to GenerationState if needed
        if isinstance(state, dict):
            state = GenerationState(**state)
            
        if state.status in ["research_failed", "generation_failed", "evaluation_failed"]:
            logger.error(f"Workflow failed with status: {state.status}")
            return "end"
        
        if state.status == "completed":
            logger.info("Workflow completed successfully")
            return "end"
        
        if len(state.generated_data) < state.num_records and state.status != "generation_completed":
            logger.info(f"Continuing generation: {len(state.generated_data)}/{state.num_records}")
            return "continue"
        
        # If we have enough data but haven't evaluated yet
        if len(state.generated_data) >= state.num_records and state.status != "completed":
            return "end"  # Go to evaluation
        
        return "end"
    
    async def run_workflow(self, domain: str, data_format: str, num_records: int, 
                          context: str = None) -> GenerationState:
        """Run the complete synthetic data generation workflow"""
        try:
            # Initialize state
            initial_state = GenerationState(
                domain=domain,
                data_format=data_format,
                num_records=num_records,
                context=context,
                status="pending"
            )
            
            logger.info(f"Starting workflow: {domain} - {data_format} - {num_records} records")
            
            # Execute workflow
            final_result = await self.workflow.ainvoke(initial_state)
            
            # Handle both dict and GenerationState returns
            if isinstance(final_result, dict):
                final_state = GenerationState(**final_result)
            else:
                final_state = final_result
            
            logger.info(f"Workflow completed with status: {final_state.status}")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return GenerationState(
                domain=domain,
                data_format=data_format,
                num_records=num_records,
                context=context,
                status="failed",
                error_message=str(e)
            )
    
    async def get_workflow_status(self, state) -> Dict[str, Any]:
        """Get current workflow status"""
        # Convert dict to GenerationState if needed
        if isinstance(state, dict):
            state = GenerationState(**state)
            
        return {
            "domain": state.domain,
            "data_format": state.data_format,
            "target_records": state.num_records,
            "generated_records": len(state.generated_data),
            "current_batch": state.current_batch,
            "total_batches": state.total_batches,
            "status": state.status,
            "progress_percentage": (len(state.generated_data) / state.num_records * 100) if state.num_records > 0 else 0,
            "file_path": state.file_path,
            "error_message": state.error_message
        }