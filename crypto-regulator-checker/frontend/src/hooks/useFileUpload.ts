import { useState } from 'react';
import axios from 'axios';

interface FileUploadState {
  isUploading: boolean;
  progress: number;
  error: Error | null;
}

interface FileUploadResponse {
  documentId: string;
  status: string;
  message?: string;
}

export const useFileUpload = () => {
  const [state, setState] = useState<FileUploadState>({
    isUploading: false,
    progress: 0,
    error: null,
  });

  const uploadFile = async (file: File): Promise<FileUploadResponse> => {
    setState(prev => ({ ...prev, isUploading: true, progress: 0, error: null }));

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<FileUploadResponse>(
        '/api/documents/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setState(prev => ({ ...prev, progress }));
          },
        }
      );

      setState(prev => ({ ...prev, isUploading: false, progress: 100 }));
      return response.data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error : new Error('Upload failed');
      setState(prev => ({
        ...prev,
        isUploading: false,
        error: errorMessage,
      }));
      throw errorMessage;
    }
  };

  const resetState = () => {
    setState({
      isUploading: false,
      progress: 0,
      error: null,
    });
  };

  return {
    uploadFile,
    resetState,
    ...state,
  };
};
