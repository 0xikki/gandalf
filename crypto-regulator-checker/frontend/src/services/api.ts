import axios from 'axios';

// Types
export interface AnalysisResult {
  status: 'compliant' | 'non-compliant' | 'warning';
  message: string;
  details: string[];
  regulations: {
    id: string;
    title: string;
    relevance: number;
    description: string;
  }[];
}

interface UploadResponse {
  documentId: string;
}

// API Configuration
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// API Service functions
export const uploadDocument = async (file: File, token: string | null) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload document');
  }

  const data = await response.json();
  return data.document_id;
};

export const getAnalysisResults = async (documentId: string, token: string | null) => {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/analysis`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get analysis results');
  }

  return response.json();
};

// Error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Axios interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      throw new ApiError(
        error.response.data.message || 'An error occurred',
        error.response.status,
        error.response.data
      );
    }
    throw new ApiError('Network error occurred');
  }
);

export default {
  uploadDocument,
  getAnalysisResults,
}; 