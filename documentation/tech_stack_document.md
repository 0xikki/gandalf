# Tech Stack Document
_Updated based on Initial Audit - March 31, 2024_

## Development Environment

### Core Tools
- **Version Control**: Git
- **IDE**: Cursor with AI assistance
- **Container Platform**: Docker with Docker Compose
- **CI/CD**: GitHub Actions (planned)

### Development Dependencies
- **Package Management**:
  - Frontend: npm/yarn
  - Backend: pip with requirements.txt
- **Code Quality**:
  - ESLint for TypeScript/JavaScript
  - Black for Python
  - Pre-commit hooks
  - Type checking (mypy for Python, TypeScript for frontend)

## Frontend Stack

### Core Technologies
- **Framework**: React 18
- **Language**: TypeScript 5.x
- **State Management**: React Context + Hooks
- **Routing**: React Router 6

### UI Components
- **Component Library**: MUI (Material-UI) v5
- **Form Handling**: React Hook Form
- **File Upload**: react-dropzone
- **Data Display**: 
  - react-table for results
  - recharts for visualizations

### API Integration
- **HTTP Client**: axios
- **WebSocket**: Socket.IO client
- **Data Validation**: zod
- **Error Handling**: Custom error boundary components

### Testing
- **Unit Testing**: Jest + React Testing Library
- **E2E Testing**: Cypress
- **Performance Testing**: Lighthouse

## Backend Stack

### Core Technologies
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ASGI Server**: uvicorn
- **Process Manager**: gunicorn

### Document Processing
- **PDF Processing**: PyPDF2
- **DOCX Processing**: python-docx
- **Text Extraction**: Textract
- **Chunking**: Custom implementation with spaCy

### LLM Integration
- **Primary Model**: Gemini Pro
- **Embeddings**: SentenceTransformers
- **Vector Store**: ChromaDB
- **Caching**: Redis

### API Layer
- **Documentation**: OpenAPI/Swagger
- **Authentication**: JWT + OAuth2
- **Rate Limiting**: FastAPI built-in + Redis
- **WebSocket**: FastAPI WebSocket support

### Storage
- **Vector Database**: ChromaDB
- **Cache**: Redis
- **File Storage**: Local filesystem (with proper security)

### Testing
- **Unit Testing**: pytest
- **Coverage**: pytest-cov
- **Mocking**: pytest-mock
- **API Testing**: pytest-asyncio

## Infrastructure

### Containerization
- **Container Runtime**: Docker
- **Orchestration**: Docker Compose
- **Base Images**: 
  - Frontend: node:20-alpine
  - Backend: python:3.11-slim
  - Cache: redis:7-alpine

### Security
- **Authentication**: JWT
- **File Validation**: python-magic
- **Rate Limiting**: Redis-based
- **CORS**: FastAPI CORS middleware
- **Input Validation**: Pydantic

### Monitoring
- **Logging**: Python logging + JSON formatter
- **Metrics**: Prometheus (planned)
- **Dashboards**: Grafana (planned)
- **Error Tracking**: Sentry (planned)

### Performance
- **Caching**: Redis
- **Load Balancing**: Nginx
- **Rate Limiting**: Redis-based
- **File Processing**: Async with proper chunking

## Development Workflow

### Code Quality
- **Linting**: 
  - ESLint + Prettier (Frontend)
  - Black + isort (Backend)
- **Type Checking**:
  - TypeScript (Frontend)
  - mypy (Backend)
- **Pre-commit Hooks**:
  - Code formatting
  - Type checking
  - Test running

### Testing Strategy
- **Unit Tests**: Required for all core functionality
- **Integration Tests**: Required for API endpoints
- **E2E Tests**: Required for critical user flows
- **Performance Tests**: Required for data processing pipelines

### Documentation
- **API**: OpenAPI/Swagger
- **Code**: Docstrings + Type hints
- **Architecture**: Draw.io diagrams
- **User Guide**: Markdown in repo

### Deployment
- **Environments**:
  - Development
  - Staging
  - Production
- **CI/CD Pipeline**:
  - Automated testing
  - Code quality checks
  - Security scanning
  - Automated deployment

## Version Requirements

### Frontend
- Node.js >= 20.0.0
- TypeScript >= 5.0.0
- React >= 18.0.0
- Material-UI >= 5.0.0

### Backend
- Python >= 3.11
- FastAPI >= 0.100.0
- ChromaDB >= 0.4.0
- Redis >= 7.0.0

### Infrastructure
- Docker >= 24.0.0
- Docker Compose >= 2.0.0
- Nginx >= 1.24.0

## Notes
- All version numbers should be pinned in respective dependency files
- Security updates should be automatically monitored
- Performance metrics should be collected from day one
- All deployments must go through the CI/CD pipeline