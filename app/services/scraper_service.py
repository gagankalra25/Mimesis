import logging
import asyncio
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
from app.config import SUPPORTED_DOMAINS

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def get_session(self):
        if not self.session:
            self.session = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.aclose()
    
    def get_search_queries(self, domain: str, context: str = None) -> List[str]:
        """Generate search queries for domain research"""
        domain_info = SUPPORTED_DOMAINS.get(domain, {})
        keywords = domain_info.get("keywords", [])
        
        base_queries = [
            f"{domain} best practices",
            f"{domain} terminology glossary",
            f"{domain} industry standards",
            f"{domain} common procedures",
            f"{domain} key concepts"
        ]
        
        # Add keyword-specific queries
        for keyword in keywords[:3]:  # Limit to top 3 keywords
            base_queries.append(f"{keyword} {domain} guide")
        
        # Add context-specific query if provided
        if context:
            base_queries.append(f"{domain} {context}")
        
        return base_queries[:5]  # Limit to 5 queries for POC
    
    async def search_and_extract(self, query: str) -> str:
        """Search for content and extract relevant information"""
        try:
            session = await self.get_session()
            
            # Use DuckDuckGo Instant Answer API (no API key required)
            search_url = f"https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = await session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            content_parts = []
            
            # Abstract
            if data.get('Abstract'):
                content_parts.append(f"Overview: {data['Abstract']}")
            
            # Related topics
            if data.get('RelatedTopics'):
                topics = data['RelatedTopics'][:3]  # Limit to 3 topics
                for topic in topics:
                    if isinstance(topic, dict) and topic.get('Text'):
                        content_parts.append(f"Related: {topic['Text']}")
            
            # Answer
            if data.get('Answer'):
                content_parts.append(f"Answer: {data['Answer']}")
            
            return " | ".join(content_parts) if content_parts else f"Basic information about {query}"
            
        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {str(e)}")
            return f"General knowledge about {query}"
    
    async def scrape_domain_info(self, domain: str, context: str = None) -> Dict[str, Any]:
        """Scrape domain information using multiple search queries"""
        try:
            queries = self.get_search_queries(domain, context)
            
            # Search for information using multiple queries
            search_tasks = [self.search_and_extract(query) for query in queries]
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Filter out exceptions and combine results
            valid_results = [
                result for result in search_results 
                if isinstance(result, str) and result.strip()
            ]
            
            if not valid_results:
                # Fallback to domain description
                domain_info = SUPPORTED_DOMAINS.get(domain, {})
                valid_results = [domain_info.get("description", f"General {domain} domain information")]
            
            # Combine all search results
            combined_info = " | ".join(valid_results)
            
            # Extract key terms and concepts
            domain_config = SUPPORTED_DOMAINS.get(domain, {})
            keywords = domain_config.get("keywords", [])
            
            return {
                "scraped_content": combined_info,
                "source_queries": queries,
                "domain_keywords": keywords,
                "search_success": len(valid_results) > 0
            }
            
        except Exception as e:
            logger.error(f"Domain scraping failed for {domain}: {str(e)}")
            
            # Fallback response
            domain_info = SUPPORTED_DOMAINS.get(domain, {})
            return {
                "scraped_content": domain_info.get("description", f"Basic {domain} information"),
                "source_queries": [],
                "domain_keywords": domain_info.get("keywords", []),
                "search_success": False
            }
    
    async def enrich_context_with_web_data(self, domain: str, base_context: str, user_context: str = None) -> str:
        """Enrich domain context with web-scraped information"""
        try:
            scraped_data = await self.scrape_domain_info(domain, user_context)
            
            enriched_context = f"""
Base Context: {base_context}

Web Research Results: {scraped_data['scraped_content']}

Domain Keywords: {', '.join(scraped_data['domain_keywords'])}
"""
            
            if user_context:
                enriched_context += f"\nUser Specific Context: {user_context}"
            
            return enriched_context.strip()
            
        except Exception as e:
            logger.error(f"Context enrichment failed: {str(e)}")
            return base_context
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()