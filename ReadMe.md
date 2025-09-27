# Synthetic Data Generator

A LangGraph-powered API for generating domain-specific synthetic datasets in various formats. Built with FastAPI, this system uses a multi-agent architecture to research, generate, and evaluate high-quality synthetic data for AI/ML applications.

## Features

- **Multi-Domain Support**: Healthcare, Finance, Business, Law, Technology, Education
- **Multiple Data Formats**: Q&A pairs, Entity relationships, RAG chunks, Fine-tuning datasets
- **React Prompting**: Advanced LLM prompting for high-quality data generation
- **Quality Assurance**: Automated deduplication and quality validation
- **Web Research**: Domain context enrichment through web scraping
- **Batch Processing**: Efficient generation of large datasets
- **File Export**: CSV output with timestamp-based naming

## Quick Start

### Using Docker (Recommended)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd synthetic-data-generator
   cp .env.example .env
   ```

2. **Configure Environment**
   Edit `.env` file:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   ENVIRONMENT=development
   ```

3. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Local Development

1. **Python Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run Application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Usage

### Generate Synthetic Data

**POST** `/generate-synthetic-data`

```json
{
  "domain": "healthcare",
  "data_format": "qna", 
  "num_records": 100,
  "context": "patient diagnosis procedures"
}
```

**Response:**
```json
{
  "status": "completed",
  "total_records": 100,
  "file_path": "responses/healthcare_qna_20241201_143022.csv",
  "generation_time": "2.5 minutes"
}
```

### Supported Domains
- `healthcare` - Medical, clinical research, patient care
- `finance` - Banking, investments, risk management  
- `business` - Strategy, operations, management
- `law` - Legal procedures, contracts, compliance
- `technology` - Software development, AI, cybersecurity
- `education` - Learning, curriculum, assessment

### Supported Formats
- `qna` - Question and answer pairs with context
- `entity_relationships` - Entity relationship mappings
- `rag_chunks` - RAG-optimized content chunks
- `fine_tuning` - Instruction-input-output format

### Additional Endpoints

- **GET** `/` - API information
- **GET** `/health` - Health check
- **GET** `/supported-domains` - List supported domains
- **GET** `/supported-formats` - List supported formats
- **GET** `/files/{file_path}` - Get file information
- **GET** `/files/{file_path}/sample` - Preview generated data
- **DELETE** `/cleanup?days_old=7` - Clean up old files

## Architecture

### LangGraph Workflow

```
Research Agent → Generator Agent → Evaluator Agent
      ↓              ↓              ↓
  Web scraping   Batch creation   Quality validation
  Domain info    (10-15 records)  & deduplication
```

### React Prompting

Each agent uses React (Reason + Act) prompting:
- **Thought**: Analyze the task requirements
- **Action**: Execute specific operations
- **Observation**: Review results and findings
- **Reflection**: Synthesize and optimize output

### Key Components

- **Research Agent**: Web scraping and domain analysis
- **Generator Agent**: Batch-wise synthetic data creation
- **Evaluator Agent**: Quality validation and deduplication
- **LLM Service**: ChatGroq integration with error handling
- **File Service**: CSV generation and management

## Configuration

### Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key_here
ENVIRONMENT=development
MAX_RECORDS_PER_REQUEST=1000
BATCH_SIZE=15
MAX_RETRIES=3
```

### LLM Models
- Primary: `llama-3.1-70b-versatile`
- Fast: `llama-3.1-8b-instant`
- Advanced: `mixtral-8x7b-32768`

## Output Examples

### Q&A Format
```csv
question,answer,context
"What is hypertension?","High blood pressure condition","Medical terminology"
```

### Entity Relationships
```csv
entity1,relationship,entity2
"Patient","diagnosed_with","Diabetes"
```

### RAG Chunks
```csv
content,metadata,summary
"Detailed medical procedure...","{'source': 'clinical_guide'}","Procedure overview"
```

### Fine-tuning Format
```csv
instruction,input,output
"Diagnose the condition","Patient shows symptoms...","Likely diagnosis is..."
```

## Testing

```bash
# Run tests
python -m pytest tests/ -v

# Test API endpoints
curl -X POST "http://localhost:8000/generate-synthetic-data" \
  -H "Content-Type: application/json" \
  -d '{"domain":"healthcare","data_format":"qna","num_records":10}'
```

## Workflow Details

### 1. Research Phase
- Web scraping for domain-specific information
- Terminology and concept extraction  
- Context enrichment for generation

### 2. Generation Phase
- Batch processing (10-15 records per call)
- Domain-aware synthetic data creation
- Format-specific schema validation

### 3. Evaluation Phase
- Duplicate detection and removal
- Quality scoring and filtering
- CSV file generation and storage

## Limitations (POC)

- Maximum 1,000 records per request
- No caching mechanism
- Local file storage only
- Limited to predefined domains
- CSV output format only

## Development

### Project Structure
```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── models/              # Pydantic schemas
├── agents/              # LangGraph agents
├── services/            # External integrations
└── utils/               # Helper functions
```

### Adding New Domains
1. Add domain to `SUPPORTED_DOMAINS` in `config.py`
2. Update domain context in `domains.py`
3. Test with sample requests

### Adding New Formats
1. Add format to `SUPPORTED_FORMATS` in `config.py`
2. Create Pydantic model in `schemas.py`
3. Update generation and validation logic

## Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure `GROQ_API_KEY` is set correctly
   - Check API key validity and credits

2. **Generation Timeout**
   - Reduce `num_records` for testing
   - Check network connectivity

3. **File Not Found**
   - Verify `responses/` directory exists
   - Check file permissions

### Logs

Application logs are available in:
- Docker: `docker-compose logs -f`
- Local: Console output

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

MIT License - see LICENSE file for details.