# QA Bot - Document Question Answering System

A Retrieval-Augmented Generation (RAG) system built with LlamaIndex, Pinecone, and OpenAI for intelligent document-based question answering.

## Features

- 📄 **PDF Document Processing**: Upload and process PDF documents with text extraction
- 🔍 **Semantic Search**: Find relevant information using vector similarity search
- 🤖 **AI-Powered Answers**: Generate contextual answers using GPT-4
- 🌐 **Web Interface**: User-friendly Streamlit web application
- 🚀 **REST API**: FastAPI backend for programmatic access
- 📊 **Query History**: Track questions and answers with confidence scores
- 🗃️ **Document Management**: Upload, view, and delete documents
- 🎯 **Configurable Search**: Adjust similarity thresholds and result counts

## Technology Stack

- **LlamaIndex 0.10+**: Document indexing and RAG orchestration
- **Pinecone**: Vector database for semantic search
- **OpenAI GPT-4**: Language model for answer generation
- **OpenAI Embeddings**: Text embedding for semantic similarity
- **Streamlit**: Web interface
- **FastAPI**: REST API framework
- **SQLAlchemy**: Database ORM
- **PyPDF**: PDF text extraction
- **Python 3.9+**

## Project Structure

```
Project/
├── src/
│   ├── core/                 # Core application logic
│   │   ├── config.py         # Configuration settings
│   │   ├── pdf_processor.py  # PDF processing utilities
│   │   ├── vector_store.py   # Pinecone vector operations
│   │   └── rag_engine.py     # RAG query engine
│   ├── database/             # Database models and operations
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── database.py       # Database configuration
│   │   └── crud.py           # CRUD operations
│   ├── ui/                   # User interface
│   │   └── streamlit_app.py  # Streamlit web application
│   └── api/                  # REST API
│       └── fastapi_app.py    # FastAPI application
├── tests/                    # Test files
├── docs/                     # Documentation
├── config/                   # Configuration files
├── static/                   # Static assets
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Setup and Installation

### 1. Environment Setup

```bash
# Clone or navigate to the project directory
cd QAbot(Llamaindex)/Project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Copy the `.env.example` file to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=qa-bot-index

# Database Configuration
DATABASE_URL=sqlite:///./qa_bot.db
```

### 3. Database Initialization

Initialize the database tables:

```bash
python main.py init-db
```

## Usage

### Web Application (Streamlit)

Run the Streamlit web interface:

```bash
python main.py streamlit
```

Then open your browser to: `http://localhost:8501`

### REST API (FastAPI)

Run the FastAPI REST API:

```bash
python main.py fastapi
```

API documentation available at: `http://localhost:8000/docs`

### Direct Python Usage

```python
from src.core.rag_engine import RAGEngine
from src.core.pdf_processor import PDFProcessor

# Initialize components
rag_engine = RAGEngine()
pdf_processor = PDFProcessor()

# Process a PDF document
pdf_result = pdf_processor.extract_text_from_pdf("document.pdf")
chunks = pdf_processor.chunk_text(pdf_result["full_text"])

# Index the document
rag_engine.process_and_index_document({"id": 1}, chunks)

# Query the system
result = rag_engine.generate_answer("What is machine learning?")
print(result["answer"])
```

## API Endpoints

### Document Management

- `POST /upload` - Upload PDF documents
- `GET /documents` - List all documents
- `DELETE /documents/{id}` - Delete a document
- `GET /documents/{id}/stats` - Get document statistics

### Query System

- `POST /query` - Ask questions about documents
- `GET /search` - Search for similar content

### System Health

- `GET /health` - Health check
- `GET /` - API information

## Configuration

Key configuration options in `src/core/config.py`:

- `chunk_size`: Token size for document chunks (default: 1024)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `similarity_top_k`: Number of relevant chunks to retrieve (default: 5)
- `confidence_threshold`: Minimum relevance score (default: 0.7)
- `max_file_size_mb`: Maximum upload size (default: 50MB)

## Features in Detail

### Document Processing

1. **PDF Upload**: Supports batch upload of PDF files up to 50MB each
2. **Text Extraction**: Uses PyPDF for robust text extraction
3. **Chunking**: Intelligent text chunking with configurable size and overlap
4. **Deduplication**: Prevents duplicate document uploads using content hashing
5. **Metadata Extraction**: Extracts document metadata (author, title, pages)

### Question Answering

1. **Semantic Search**: Vector similarity search using OpenAI embeddings
2. **Context Assembly**: Retrieves and ranks relevant document chunks
3. **Answer Generation**: Uses GPT-4 to generate contextual answers
4. **Source Attribution**: Provides references to source documents and pages
5. **Confidence Scoring**: Returns confidence scores for answer quality

### Web Interface

1. **Document Upload**: Drag-and-drop PDF upload interface
2. **Question Input**: Natural language question input
3. **Answer Display**: Formatted answers with source references
4. **Query History**: Track recent questions and answers
5. **Document Library**: View and manage uploaded documents
6. **Settings Panel**: Adjust search parameters dynamically

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Troubleshooting

### Common Issues

1. **Pinecone Connection Error**
   - Verify your Pinecone API key and environment
   - Check if the index name is correct

2. **OpenAI API Error**
   - Ensure your OpenAI API key is valid
   - Check your API usage limits

3. **PDF Processing Error**
   - Verify PDF files are not corrupted
   - Some PDFs may have text extraction issues

4. **Memory Issues**
   - Reduce `chunk_size` for large documents
   - Process fewer documents simultaneously

### Logs and Debugging

Enable debug mode in `.env`:

```env
DEBUG=true
```

Check application logs for detailed error information.

## Performance Optimization

1. **Chunking Strategy**: Optimize chunk size based on your documents
2. **Embedding Caching**: Consider caching embeddings for large documents
3. **Database Indexing**: Add indexes for frequently queried fields
4. **Vector Store**: Monitor Pinecone usage and optimize queries

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **File Validation**: Validate uploaded files thoroughly
3. **Input Sanitization**: Sanitize user inputs to prevent injection
4. **Access Control**: Implement proper authentication for production use

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions and support:

1. Check the documentation
2. Review common issues in troubleshooting
3. Open an issue on the repository