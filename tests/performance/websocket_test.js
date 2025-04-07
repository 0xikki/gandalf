import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import http from 'k6/http';

// Custom metrics
const wsFailureRate = new Rate('websocket_failures');
const wsLatency = new Rate('websocket_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up to 10 users
    { duration: '1m', target: 10 },  // Stay at 10 users
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    'websocket_failures': ['rate<0.1'],    // Less than 10% failures
    'websocket_latency': ['p(95)<100'],    // 95% of messages under 100ms latency
  },
};

export default function () {
  const BASE_URL = 'http://localhost:8000/api';
  
  // First get an auth token
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'test-password',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(loginRes, {
    'login successful': (r) => r.status === 200,
    'has access token': (r) => r.json('access_token') !== undefined,
  });
  
  const token = loginRes.json('access_token');
  
  // Connect to WebSocket
  const url = 'ws://localhost:8000/ws/documents/1';
  const params = { 
    headers: { 'Authorization': `Bearer ${token}` },
  };

  const res = ws.connect(url, params, function (socket) {
    socket.on('open', () => {
      console.log('WebSocket connection established');
      
      // Send authentication message
      socket.send(JSON.stringify({
        type: 'auth',
        token: token
      }));
    });

    socket.on('message', (data) => {
      const message = JSON.parse(data);
      const now = Date.now();
      
      if (message.timestamp) {
        // Calculate latency for messages with timestamps
        const latency = now - message.timestamp;
        wsLatency.add(latency);
      }
      
      // Check message type and handle accordingly
      if (message.type === 'status') {
        check(message, {
          'status message has document id': (obj) => obj.documentId !== undefined,
          'status message has progress': (obj) => obj.progress !== undefined,
        }) || wsFailureRate.add(1);
      }
    });

    socket.on('error', (e) => {
      console.error('WebSocket error:', e);
      wsFailureRate.add(1);
    });

    // Keep connection alive for test duration
    socket.setInterval(() => {
      socket.send(JSON.stringify({ type: 'ping' }));
    }, 1000);
  });

  check(res, {
    'WebSocket connection successful': (r) => r && r.status === 101,
  }) || wsFailureRate.add(1);

  sleep(10); // Keep connection open for 10 seconds per VU
} 