import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from './useAuth';

interface WebSocketMessage {
  type: string;
  documentId: number;
  status: string;
  progress?: number;
  error?: string;
}

const DEBUG = process.env.NODE_ENV === 'development';

const log = {
  debug: (...args: any[]) => DEBUG && console.debug('[WebSocket]', ...args),
  info: (...args: any[]) => DEBUG && console.info('[WebSocket]', ...args),
  warn: (...args: any[]) => DEBUG && console.warn('[WebSocket]', ...args),
  error: (...args: any[]) => console.error('[WebSocket]', ...args)
};

export const useDocumentWebSocket = (
  documentId: number,
  onStatusUpdate: (status: string, progress?: number) => void,
  onError: (error: string) => void
) => {
  const wsRef = useRef<WebSocket | null>(null);
  const { token } = useAuth();
  
  const connect = useCallback(() => {
    log.debug('Initiating WebSocket connection');
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log.debug('WebSocket already connected');
      return;
    }

    try {
      const ws = new WebSocket(`${process.env.REACT_APP_WS_URL}/documents/${documentId}`);
      wsRef.current = ws;
      log.info('WebSocket connection created');

      ws.onopen = () => {
        log.info('WebSocket connection opened');
        // Send authentication
        ws.send(JSON.stringify({ type: 'auth', token }));
      };

      ws.onmessage = (event) => {
        try {
          log.debug('Received WebSocket message:', event.data);
          const message: WebSocketMessage = JSON.parse(event.data);
          
          switch (message.type) {
            case 'status':
              log.info(`Status update for document ${documentId}:`, message.status);
              onStatusUpdate(message.status, message.progress);
              break;
            case 'error':
              log.warn(`Error for document ${documentId}:`, message.error);
              onError(message.error || 'Unknown error occurred');
              break;
            default:
              log.warn('Unknown message type:', message.type);
          }
        } catch (error) {
          log.error('Error processing WebSocket message:', error);
          onError('Error processing server message');
        }
      };

      ws.onerror = (error) => {
        log.error('WebSocket error:', error);
        onError('Connection error occurred');
      };

      ws.onclose = () => {
        log.info('WebSocket connection closed');
        // Attempt to reconnect after delay
        setTimeout(() => {
          log.debug('Attempting to reconnect...');
          connect();
        }, 5000);
      };

    } catch (error) {
      log.error('Error creating WebSocket connection:', error);
      onError('Failed to establish connection');
    }
  }, [documentId, token, onStatusUpdate, onError]);

  useEffect(() => {
    log.debug('Setting up WebSocket connection');
    connect();

    return () => {
      log.debug('Cleaning up WebSocket connection');
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log.debug('Sending message:', message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      log.warn('Cannot send message - WebSocket not connected');
      onError('Connection not available');
    }
  }, [onError]);

  return { sendMessage };
}; 