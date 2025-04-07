# Crypto Regulator Checker

A powerful tool for analyzing cryptocurrency regulations and compliance requirements using advanced NLP and RAG (Retrieval Augmented Generation) techniques.

## Features

- Document Processing: Handles various document formats (PDF, DOCX, HTML) for regulatory text analysis
- Semantic Search: Uses state-of-the-art embeddings for accurate information retrieval
- RAG Pipeline: Combines vector search with LLM capabilities for precise answers
- Caching System: Redis-based caching with local fallback for optimal performance
- Structured Logging: Comprehensive logging system for monitoring and debugging
- Error Handling: Robust error management system with custom exceptions
- Configuration Management: Centralized configuration using Pydantic
- Testing Infrastructure: Extensive test coverage with pytest

## Project Structure

```
├── backend/                   # Backend server application
│   ├── src/                  # Source code
│   │   ├── core/            # Core functionality
│   │   │   ├── cache.py     # Caching implementation
│   │   │   ├── exceptions.py # Base exception classes
│   │   │   ├── logging.py   # Structured logging setup
│   │   │   └── config.py    # Global configuration
│   │   ├── document_processing/
│   │   ├── embeddings/
│   │   ├── vector_store/
│   │   ├── llm/
│   │   ├── rag/
│   │   └── main.py
│   ├── tests/               # Test suite
│   ├── requirements/        # Dependencies
│   └── logging.ini         # Logging configuration
├── frontend/               # Frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   │   ├── common/   # Shared components
│   │   │   ├── layout/   # Layout components
│   │   │   └── forms/    # Form components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API integration services
│   │   ├── utils/        # Utility functions
│   │   ├── styles/       # Global styles and themes
│   │   ├── types/        # TypeScript type definitions
│   │   └── App.tsx       # Root component
│   ├── public/           # Static assets
│   ├── tests/            # Frontend tests
│   └── package.json      # Frontend dependencies
├── shared/               # Shared code between frontend and backend
│   ├── types/           # Shared TypeScript/Python types
│   ├── constants/       # Shared constants
│   └── utils/           # Shared utility functions
├── docs/                # Documentation
│   ├── backend/         # Backend documentation
│   ├── frontend/        # Frontend documentation
│   └── api/            # API documentation
├── scripts/            # Development and deployment scripts
├── .github/            # GitHub configuration
│   └── workflows/      # GitHub Actions workflows
├── .env.example        # Example environment variables
├── docker-compose.yml  # Docker compose configuration
├── Dockerfile         # Docker configuration
├── README.md          # Project documentation
└── LICENSE           # License information
```

## Technology Stack

### Backend
- Python 3.11+
- FastAPI - Web framework
- Pydantic - Data validation
- SQLAlchemy - ORM
- Redis - Caching
- pytest - Testing

### Frontend
- TypeScript 5.0+
- React 18
- Vite - Build tool
- TailwindCSS - Styling
- React Query - Data fetching
- Vitest - Testing
- ESLint/Prettier - Code formatting

### Infrastructure
- Docker - Containerization
- Redis - Caching
- PostgreSQL - Database
- nginx - Reverse proxy

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn backend.main:app --reload
```

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
pip install -r requirements/dev.txt
uvicorn src.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running with Docker
```bash
docker-compose up -d
```

### Code Quality

#### Backend
```bash
# Run tests
pytest tests/ -v --cov=src

# Type checking
mypy src/

# Linting
flake8 src/

# Format code
black src/
isort src/
```

#### Frontend
```bash
# Run tests
npm run test

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

## Configuration

Key configuration parameters in `.env`:

```
# Core
ENVIRONMENT=development
LOG_LEVEL=INFO

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Vector Store
VECTOR_STORE_PATH=./data/vector_store

# LLM
GOOGLE_API_KEY=your_api_key
MODEL_NAME=gemini-pro
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License 