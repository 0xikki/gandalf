# Performance Tests

This directory contains performance tests for the Crypto Regulator Checker API using k6.

## Prerequisites

1. Install k6: https://k6.io/docs/getting-started/installation/
2. Ensure the API server is running locally on port 8000

## Test Scripts

### 1. API Load Test (`load_test.js`)

Tests the core API endpoints under load:
- User registration
- User login
- Document upload
- Document listing

To run:
```bash
k6 run load_test.js
```

Performance criteria:
- 95% of requests must complete under 500ms
- Less than 10% failure rate
- Ramps up to 20 concurrent users over 5 minutes

### 2. WebSocket Test (`websocket_test.js`)

Tests the WebSocket functionality:
- Connection establishment
- Authentication
- Real-time status updates
- Message latency

To run:
```bash
k6 run websocket_test.js
```

Performance criteria:
- 95% of messages must have latency under 100ms
- Less than 10% connection failures
- Ramps up to 10 concurrent connections over 2 minutes

## Test Environment Setup

Before running tests:

1. Start the API server in test mode:
   ```bash
   cd ../../
   python -m uvicorn src.main:app --port 8000
   ```

2. Create a test user:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test-password"}'
   ```

## Interpreting Results

The test output will show:
- Virtual user (VU) metrics
- Response time percentiles
- Error rates
- Custom metrics (e.g., WebSocket latency)

A test is considered successful if it meets all threshold criteria defined in the test configuration. 