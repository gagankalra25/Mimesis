import logging
from typing import Dict, Any
from models.schemas import GenerationState, ResearchResult
from services.llm_service import LLMService
from services.scraper_service import ScraperService
from models.domains import DomainConfig

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.scraper_service = ScraperService()
        self.domain_config = DomainConfig()
    
    async def research_domain(self, state: GenerationState) -> GenerationState:
        """Research domain knowledge using web scraping and LLM analysis"""
        try:
            logger.info(f"Starting domain research for: {state.domain}")
            
            # Get base domain context
            base_context = self.domain_config.get_domain_context(state.domain, state.context)
            
            # Enrich context with web-scraped data
            async with self.scraper_service as scraper:
                enriched_context = await scraper.enrich_context_with_web_data(
                    state.domain, base_context, state.context
                )
            
            # Use LLM to analyze and structure the research
            research_data = await self.llm_service.research_domain(state.domain, enriched_context)
            
            # Create research result
            research_result = ResearchResult(
                domain_info=research_data.get("domain_info", enriched_context),
                key_concepts=research_data.get("key_concepts", []),
                terminology=research_data.get("terminology", []),
                context_enriched=research_data.get("context_enriched", enriched_context)
            )
            
            # Update state with research findings
            state.domain_research = research_result.model_dump_json()
            state.status = "research_completed"
            
            logger.info(f"Domain research completed for: {state.domain}")
            return state
            
        except Exception as e:
            logger.error(f"Domain research failed: {str(e)}")
            state.status = "research_failed"
            state.error_message = f"Research failed: {str(e)}"
            return state
    
    async def __call__(self, state: GenerationState) -> GenerationState:
        """Main entry point for the research agent"""
        return await self.research_domain(state)