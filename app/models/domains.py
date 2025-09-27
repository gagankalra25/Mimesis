from typing import Dict, List

class DomainConfig:
    """Domain-specific configurations for synthetic data generation"""
    
    @staticmethod
    def get_research_sources(domain: str) -> List[str]:
        """Get domain-specific research sources"""
        sources = {
            "healthcare": [
                "medical journals and publications",
                "clinical research databases",
                "healthcare guidelines and protocols",
                "medical terminology resources",
                "patient care standards"
            ],
            "finance": [
                "financial regulations and compliance",
                "investment and trading platforms",
                "banking procedures and policies",
                "risk management frameworks",
                "financial market analysis"
            ],
            "business": [
                "business strategy frameworks",
                "management best practices",
                "operational procedures",
                "marketing and sales methodologies",
                "entrepreneurship resources"
            ],
            "law": [
                "legal statutes and regulations",
                "court procedures and protocols",
                "contract law and agreements",
                "compliance and regulatory frameworks",
                "legal precedents and case studies"
            ],
            "technology": [
                "software development practices",
                "AI and machine learning concepts",
                "cybersecurity frameworks",
                "cloud computing architectures",
                "technology standards and protocols"
            ],
            "education": [
                "pedagogical methodologies",
                "curriculum development frameworks",
                "educational assessment techniques",
                "learning technologies and tools",
                "educational psychology research"
            ]
        }
        return sources.get(domain, [])
    
    @staticmethod
    def get_domain_context(domain: str, user_context: str = None) -> str:
        """Generate rich domain context for research"""
        base_contexts = {
            "healthcare": """Healthcare domain encompasses medical practice, patient care, clinical research, 
            pharmaceutical development, medical devices, healthcare administration, and public health initiatives. 
            Key areas include diagnosis, treatment protocols, preventive care, medical ethics, and healthcare technology.""",
            
            "finance": """Finance domain covers banking services, investment management, financial planning, 
            risk assessment, insurance, regulatory compliance, and financial markets. Key areas include 
            portfolio management, credit analysis, financial modeling, and regulatory frameworks.""",
            
            "business": """Business domain includes strategic planning, operations management, marketing, 
            sales, human resources, and organizational development. Key areas include business models, 
            competitive analysis, process optimization, and stakeholder management.""",
            
            "law": """Legal domain encompasses various practice areas including corporate law, litigation, 
            regulatory compliance, contract negotiation, and legal advisory services. Key areas include 
            legal research, case analysis, document preparation, and client representation.""",
            
            "technology": """Technology domain includes software development, system architecture, 
            cybersecurity, artificial intelligence, cloud computing, and emerging technologies. 
            Key areas include programming, system design, security protocols, and technology innovation.""",
            
            "education": """Education domain covers teaching methodologies, curriculum design, student assessment, 
            educational technology, and academic administration. Key areas include learning theories, 
            instructional design, educational psychology, and institutional management."""
        }
        
        base_context = base_contexts.get(domain, "")
        if user_context:
            return f"{base_context} Specific focus: {user_context}"
        return base_context