import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const failureRate = new Rate('failed_requests');

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 20 }, // Ramp up to 20 users
    { duration: '3m', target: 20 }, // Stay at 20 users
    { duration: '1m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    'failed_requests': ['rate<0.1'], // Less than 10% failures
    'http_req_duration': ['p(95)<500'], // 95% of requests must complete below 500ms
  },
};

// Simulated user behavior
export default function () {
  const BASE_URL = 'http://localhost:8000/api';
  const payload = JSON.stringify({
    email: `test${Math.random()}@example.com`,
    password: 'test-password',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Test registration
  let res = http.post(`${BASE_URL}/auth/register`, payload, params);
  check(res, {
    'registration successful': (r) => r.status === 201,
  }) || failureRate.add(1);

  sleep(1);

  // Test login
  res = http.post(`${BASE_URL}/auth/login`, payload, params);
  check(res, {
    'login successful': (r) => r.status === 200,
    'has access token': (r) => r.json('access_token') !== undefined,
  }) || failureRate.add(1);

  // Get token for authenticated requests
  const token = res.json('access_token');
  params.headers['Authorization'] = `Bearer ${token}`;

  sleep(1);

  // Test document upload (using a small text file)
  const testDoc = 'test content for performance testing';
  const binFile = new Uint8Array(testDoc.split('').map(c => c.charCodeAt(0)));
  
  res = http.post(`${BASE_URL}/documents/upload`, {
    file: http.file(binFile, 'test.txt', 'text/plain')
  }, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  check(res, {
    'document upload successful': (r) => r.status === 201,
    'has document id': (r) => r.json('document_id') !== undefined,
  }) || failureRate.add(1);

  sleep(1);

  // Test document list
  res = http.get(`${BASE_URL}/documents`, params);
  check(res, {
    'document list successful': (r) => r.status === 200,
    'documents is array': (r) => Array.isArray(r.json()),
  }) || failureRate.add(1);

  sleep(1);
} 