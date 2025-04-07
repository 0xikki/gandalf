import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { DocumentStatus } from './DocumentStatus';
import { act } from 'react-dom/test-utils';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock WebSocket
class MockWebSocket {
  onmessage: ((event: any) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: any) => void) | null = null;
  close = vi.fn();

  constructor(public url: string) {}

  // Helper to simulate receiving a message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  simulateError(error: any) {
    if (this.onerror) {
      this.onerror(error);
    }
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any;

describe('DocumentStatus Integration', () => {
  let mockWs: MockWebSocket;

  beforeEach(() => {
    mockFetch.mockClear();
    mockFetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'pending' })
      })
    );
  });

  it('displays initial loading state', async () => {
    render(<DocumentStatus documentId="123" />);
    expect(screen.getByText(/loading document status/i)).toBeInTheDocument();
  });

  it('shows document status updates from WebSocket', async () => {
    render(<DocumentStatus documentId="123" />);

    await waitFor(() => {
      mockWs = (global.WebSocket as any).mock.instances[0];
    });

    act(() => {
      mockWs.simulateMessage({
        status: 'processing',
        progress: 50,
        message: 'Processing document...'
      });
    });

    expect(screen.getByText(/processing/i)).toBeInTheDocument();
    expect(screen.getByText(/50%/i)).toBeInTheDocument();
    expect(screen.getByText(/processing document/i)).toBeInTheDocument();
  });

  it('handles WebSocket errors gracefully', async () => {
    render(<DocumentStatus documentId="123" />);

    await waitFor(() => {
      mockWs = (global.WebSocket as any).mock.instances[0];
    });

    act(() => {
      mockWs.simulateError(new Error('Connection failed'));
    });

    expect(screen.getByText(/failed to connect/i)).toBeInTheDocument();
  });

  it('shows completion status', async () => {
    render(<DocumentStatus documentId="123" />);

    await waitFor(() => {
      mockWs = (global.WebSocket as any).mock.instances[0];
    });

    act(() => {
      mockWs.simulateMessage({
        status: 'completed',
        message: 'Document processed successfully',
        lastUpdated: new Date().toISOString()
      });
    });

    expect(screen.getByText(/completed/i)).toBeInTheDocument();
    expect(screen.getByText(/processed successfully/i)).toBeInTheDocument();
    expect(screen.getByText(/last updated/i)).toBeInTheDocument();
  });

  it('cleans up WebSocket connection on unmount', async () => {
    const { unmount } = render(<DocumentStatus documentId="123" />);

    await waitFor(() => {
      mockWs = (global.WebSocket as any).mock.instances[0];
    });

    unmount();
    expect(mockWs.close).toHaveBeenCalled();
  });
}); 