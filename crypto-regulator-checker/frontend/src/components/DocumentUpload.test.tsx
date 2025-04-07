import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentUploadForm } from './DocumentUploadForm';
import { act } from 'react-dom/test-utils';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('DocumentUploadForm Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('validates file selection and shows feedback', async () => {
    render(<DocumentUploadForm onSuccess={vi.fn()} />);

    // Initially submit button should be disabled
    const submitButton = screen.getByRole('button', { name: /upload/i });
    expect(submitButton).toBeDisabled();

    // Create a mock PDF file
    const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/choose file/i);

    await act(async () => {
      userEvent.upload(input, file);
    });

    // Submit button should be enabled after valid file selection
    expect(submitButton).not.toBeDisabled();

    // Should show file name
    expect(screen.getByText(/test\.pdf/i)).toBeInTheDocument();
  });

  it('handles successful file upload', async () => {
    const onSuccess = vi.fn();
    render(<DocumentUploadForm onSuccess={onSuccess} />);

    const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/choose file/i);
    const description = screen.getByLabelText(/description/i);

    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ documentId: '123' })
      })
    );

    await act(async () => {
      userEvent.upload(input, file);
      fireEvent.change(description, { target: { value: 'Test description' } });
      fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith('123');
    });

    // Form should be reset
    expect(input.files).toHaveLength(0);
    expect(description).toHaveValue('');
  });

  it('displays error message on upload failure', async () => {
    render(<DocumentUploadForm onSuccess={vi.fn()} />);

    const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/choose file/i);

    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 500
      })
    );

    await act(async () => {
      userEvent.upload(input, file);
      fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/failed to upload document/i)).toBeInTheDocument();
    });
  });

  it('validates file type restrictions', async () => {
    render(<DocumentUploadForm onSuccess={vi.fn()} />);

    const invalidFile = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/choose file/i);

    await act(async () => {
      userEvent.upload(input, invalidFile);
    });

    expect(screen.getByText(/only pdf and docx files are allowed/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload/i })).toBeDisabled();
  });
}); 