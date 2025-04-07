# LLM Integration Documentation

## Overview
This document outlines the integration of Large Language Models (LLMs) with a Retrieval Augmented Generation (RAG) system for document analysis in the Crypto Regulator Checker project. The system uses Google's Gemini Pro as the default provider for document understanding, combined with a RAG system for regulatory compliance validation.

## Architecture

### Multi-Step Analysis System
```typescript
interface DocumentProcessor {
    // Step 1: Initial document analysis
    extractContent(document: Document): Promise<ExtractionResult>;
    // Step 2: RAG-based validation
    validateWithRegulations(extraction: ExtractionResult): Promise<ValidationResult>;
    // Step 3: Final analysis compilation
    generateComplianceReport(validation: ValidationResult): Promise<ComplianceReport>;
}

interface RAGSystem {
    // Regulatory knowledge base operations
    queryRegulations(context: string): Promise<RelevantRegulations>;
    updateKnowledgeBase(regulations: RegulatoryUpdate): Promise<void>;
    validateCompliance(document: ExtractionResult): Promise<ComplianceResult>;
}

class GeminiProcessor implements DocumentProcessor {
    // Gemini Pro implementation for document processing
}
```

### Configuration
```typescript
interface SystemConfig {
    llmProvider: {
        type: "gemini-pro";  // Using Pro for better accuracy
        apiKey?: string;
        options: {
            maxTokens?: number;
            temperature?: number;
        };
    };
    ragSystem: {
        vectorStore: "chroma" | "pinecone";
        updateFrequency: number;
        similarityThreshold: number;
    };
    cache: {
        duration: number;
        strategy: "time-based" | "version-based";
    };
}
```

## Implementation Details

### Processing Pipeline
1. Document Analysis (Gemini Pro)
   - Extract key regulatory points
   - Identify compliance factors
   - Structure information for validation

2. RAG System Integration
   - Query regulatory knowledge base
   - Compare extracted points with regulations
   - Identify potential compliance issues

3. Final Analysis
   - Combine LLM and RAG results
   - Generate comprehensive report
   - Highlight specific concerns

### Knowledge Base Management
- **Storage**: Vector database (Chroma/Pinecone)
- **Updates**: Regular regulatory updates
- **Indexing**: Efficient similarity search
- **Versioning**: Track regulation changes

### Default Provider (Gemini Pro)
- **Setup**: Uses Google's Generative AI SDK
- **Authentication**: Requires API key from Google Cloud Console
- **Rate Limits**: Managed per project basis
- **Costs**: Free tier available (as of implementation)

### Document Processing Flow
1. Text Extraction
   - PDF: Use pdf2text
   - DOCX: Use python-docx
   - Plain text fallback

2. Content Chunking
   - Segment by natural breaks
   - Maintain context windows
   - Handle overlapping content

3. Analysis Pipeline
   - Document preprocessing
   - LLM query construction
   - Response processing
   - Result aggregation

### Caching System
- **Storage**: Redis/SQLite
- **Key Format**: `{document_id}:{provider}:{version}`
- **Invalidation**: Time-based or on document update
- **Compression**: For large responses

## API Endpoints

### /api/v1/analyze
```json
POST /api/v1/analyze
{
    "documentId": "uuid",
    "provider": "gemini",  // optional
    "options": {
        "detailed": boolean,
        "focus": ["regulations", "risks", "compliance"]
    }
}
```

### /api/v1/llm/config
```json
POST /api/v1/llm/config
{
    "provider": "gemini",
    "apiKey": "your-api-key",
    "options": {
        "temperature": 0.7,
        "maxTokens": 1000
    }
}
```

## Error Handling

### Provider Errors
- Rate limiting exceeded
- Invalid API key
- Service unavailable
- Malformed response

### System Errors
- Document processing failed
- Cache errors
- Configuration issues
- Network timeouts

## Performance Optimization

### Two-Stage Processing
1. Initial Analysis (Gemini Pro)
   - Fast document understanding
   - Key point extraction
   - Structural analysis

2. RAG Validation
   - Deep regulatory comparison
   - Compliance verification
   - Historical context checking

### Caching Strategy
- Cache both LLM and RAG results
- Invalidate on regulatory updates
- Maintain version history
- Optimize storage usage

## Performance Considerations

### Optimization Strategies
1. Response Caching
   - Cache hit ratio target: >80%
   - Invalidation strategy
   - Compression for large responses

2. Request Batching
   - Group similar requests
   - Share context when possible
   - Optimize token usage

3. Resource Management
   - Memory usage monitoring
   - Concurrent request limiting
   - Background job queuing

## Security

### API Key Management
- Encrypted storage
- Key rotation support
- Access logging
- Validation checks

### Data Protection
- Document encryption
- Secure transmission
- Access control
- Audit logging

## Monitoring

### Metrics
- Response times
- Cache hit rates
- Error rates
- Token usage
- Cost tracking

### Alerts
- Rate limit warnings
- Error spikes
- Performance degradation
- Cost thresholds

## Future Considerations

### Planned Providers
- OpenAI GPT
- Anthropic Claude
- Local models

### Improvements
- Streaming responses
- Better caching strategies
- Enhanced error recovery
- Cost optimization 