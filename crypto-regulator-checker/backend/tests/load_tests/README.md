# Load Testing Suite

This directory contains load tests for the Crypto Regulator Checker backend services.

## Prerequisites

1. Install k6 by downloading the standalone binary from [k6 Releases](https://github.com/grafana/k6/releases)
2. Extract the binary and add it to your PATH
3. Ensure the backend server is running on `localhost:8000`

## Available Tests

### WebSocket Load Test (`websocket_test.js`)

Tests the WebSocket functionality under load:
- Simulates 10 concurrent users
- Each user:
  - Establishes a WebSocket connection
  - Authenticates
  - Sends document updates
  - Responds to heartbeats
  - Maintains connection for 30 seconds

#### Metrics Tracked
- WebSocket errors
- Messages sent
- Messages received
- Connection status

#### Success Criteria
- Less than 10 WebSocket errors
- At least 100 messages sent
- At least 100 messages received
- All connections established successfully (status 101)

## Running Tests

1. Start the backend server:
   ```powershell
   cd ../..  # Go to backend root
   uvicorn src.main:app --reload
   ```

2. In a new terminal, run the WebSocket test:
   ```powershell
   k6 run tests/load_tests/websocket_test.js
   ```

## Test Results

The test will output:
- Number of successful/failed iterations
- Custom metrics (errors, messages sent/received)
- Response time percentiles
- WebSocket connection statistics

## Troubleshooting

If you encounter PATH issues with k6:
1. Create a directory for k6 (e.g., `C:\k6`)
2. Extract k6.exe to this directory
3. Add the directory to your PATH:
   ```powershell
   $env:Path += ";C:\k6"
   ``` 