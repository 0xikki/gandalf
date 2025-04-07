# Backend Service

This directory contains the backend service for the Crypto Regulatory Compliance Checker.

## Directory Structure

```
backend/
├── src/             # Source code directory
│   ├── core/        # Core functionality (config, logging, exceptions)
│   ├── document_processing/  # Document handling and text extraction
│   ├── embeddings/          # Text embedding generation
│   ├── llm/                # LLM service integration
│   │   ├── providers/     # LLM provider implementations
│   │   └── utils/        # LLM-specific utilities
│   ├── rag/                # Retrieval Augmented Generation system
│   ├── vector_store/       # Vector database operations
│   └── main.py            # Main application entry point
├── tests/           # Test files and test utilities
├── uploads/         # Temporary storage for uploaded files
│   ├── temp/        # Temporary storage during processing
│   └── processed/   # Successfully processed files
└── requirements/    # Dependency management
    ├── base.txt     # Core dependencies
    ├── dev.txt      # Development dependencies
    └── prod.txt     # Production dependencies
```

## Service Architecture

The backend follows a modular architecture with clear separation of concerns:

1. **Core Layer** (`src/core/`)
   - Configuration management
   - Logging and error handling
   - Common exceptions and utilities
   - Caching mechanisms

2. **Document Processing** (`src/document_processing/`)
   - File upload handling
   - Text extraction and preprocessing
   - Document chunking and segmentation

3. **Embedding Layer** (`src/embeddings/`)
   - Text embedding generation
   - Embedding model management
   - Vector transformation utilities

4. **LLM Integration** (`src/llm/`)
   - LLM provider abstraction
   - Context augmentation
   - Response caching and rate limiting
   - Multiple provider support (e.g., Gemini)

5. **RAG System** (`src/rag/`)
   - Query processing
   - Context retrieval
   - Answer generation
   - Response synthesis

6. **Vector Store** (`src/vector_store/`)
   - Vector database operations
   - Multiple backend support (e.g., ChromaDB)
   - Memory-based fallback
   - Embedding persistence

Each module follows a consistent structure:
- `router.py`: API endpoints and route handlers
- `service.py`: Business logic implementation
- `schemas.py`: Data models and validation
- `exceptions.py`: Module-specific exceptions

## Dependencies

The backend uses several key dependencies:

- Flask: Web framework
- ChromaDB: Vector database
- Sentence Transformers: Text embedding generation
- Google Generative AI: LLM integration
- Redis: Caching and rate limiting

Dependencies are organized into three categories:
- `base.txt`: Core dependencies required for all environments
- `dev.txt`: Additional tools for development (testing, linting, etc.)
- `prod.txt`: Production-specific dependencies

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   python src/main.py
   ```

## Testing

Run tests using pytest:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=src tests/
```

## API Documentation

API endpoints are documented using OpenAPI/Swagger. Once the server is running, visit:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc` 