import ws from 'k6/ws';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

// Custom metrics
const websocketErrors = new Counter('websocket_errors');
const messagesSent = new Counter('messages_sent');
const messagesReceived = new Counter('messages_received');

// Test configuration
export const options = {
    vus: 10,  // Number of virtual users
    duration: '30s',  // Test duration
    thresholds: {
        'websocket_errors': ['count<10'],  // Less than 10 WebSocket errors
        'messages_sent': ['count>100'],    // At least 100 messages sent
        'messages_received': ['count>100'], // At least 100 messages received
    },
};

// Test data - token signed with "test-secret-key-for-testing-only"
const TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxOTk5OTk5OTk5fQ.eeZCKDR_8bEBOKjhN5GHFnXJUDJVHvVRVsl6YeJX7Eo';
const TEST_DOCUMENT_ID = 1;

export default function () {
    const url = 'ws://localhost:8000/ws/' + TEST_DOCUMENT_ID;
    let authenticated = false;
    
    const response = ws.connect(url, {}, function (socket) {
        // Track connection success
        check(socket, { 'connected': (s) => s !== null });
        
        // Set up connection timeout
        const connectionTimeout = setTimeout(() => {
            console.error('Connection timeout');
            socket.close();
        }, 5000); // 5 seconds timeout
        
        socket.on('open', () => {
            clearTimeout(connectionTimeout);
            
            // Send authentication message
            const authMessage = {
                type: 'authenticate',
                token: TEST_TOKEN
            };
            console.log('Sending auth message:', JSON.stringify(authMessage));
            socket.send(JSON.stringify(authMessage));
            messagesSent.add(1);
        });
        
        socket.on('message', (data) => {
            try {
                const message = JSON.parse(data);
                console.log('Received message:', JSON.stringify(message));
                messagesReceived.add(1);
                
                if (message.type === 'connection_established') {
                    authenticated = true;
                    console.log('Authentication successful');
                    
                    // Start sending document updates
                    const updateInterval = setInterval(() => {
                        if (!authenticated) {
                            clearInterval(updateInterval);
                            return;
                        }
                        
                        socket.send(JSON.stringify({
                            type: 'document_update',
                            content: 'Test content update ' + new Date().toISOString()
                        }));
                        messagesSent.add(1);
                    }, 1000); // Send update every second
                    
                    // Clear interval before test ends
                    setTimeout(() => {
                        clearInterval(updateInterval);
                    }, 29000);
                } else if (message.type === 'document_status') {
                    check(message, {
                        'document update confirmed': (m) => m.status === 'updated'
                    });
                } else if (message.type === 'heartbeat') {
                    // Respond to heartbeat
                    socket.send(JSON.stringify({ type: 'heartbeat' }));
                    messagesSent.add(1);
                } else if (message.type === 'error') {
                    websocketErrors.add(1);
                    console.error('Server error:', message.error);
                }
            } catch (e) {
                console.error('Error processing message:', e);
                websocketErrors.add(1);
            }
        });
        
        socket.on('error', (e) => {
            console.error('WebSocket error:', e);
            websocketErrors.add(1);
            authenticated = false;
        });
        
        socket.on('close', (code, reason) => {
            console.log(`WebSocket closed with code ${code} and reason: ${reason}`);
            authenticated = false;
            if (code === 1008) {
                console.error('Policy violation - check authentication and document access');
                websocketErrors.add(1);
            }
        });
        
        // Keep the connection alive for the duration of the test
        socket.setTimeout(function () {
            socket.close();
        }, 29000); // Close just before the test duration ends
    });
    
    check(response, { 'status is 101': (r) => r && r.status === 101 });
} 