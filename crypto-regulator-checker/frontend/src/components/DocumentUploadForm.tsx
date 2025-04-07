import React, { useState, useRef } from 'react';
import { Button, TextField, Box, Typography, CircularProgress } from '@mui/material';
import { useFormValidation } from '../hooks/useFormValidation';
import { withErrorHandling } from '../hoc/withErrorHandling';

interface DocumentUploadFormProps {
  onSuccess: (documentId: string) => void;
}

const ALLOWED_FILE_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const DocumentUploadForm: React.FC<DocumentUploadFormProps> = ({ onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { validate, errors } = useFormValidation({
    rules: {
      file: {
        required: true,
        validate: (file: File) => {
          if (!ALLOWED_FILE_TYPES.includes(file.type)) {
            return 'Only PDF and DOCX files are allowed';
          }
          if (file.size > MAX_FILE_SIZE) {
            return 'File size must be less than 10MB';
          }
          return true;
        }
      },
      description: {
        required: true,
        minLength: 10,
        maxLength: 500
      }
    }
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      const validationResult = validate('file', selectedFile);
      if (validationResult === true) {
        setFile(selectedFile);
        setError(null);
      } else {
        setFile(null);
        setError(validationResult as string);
      }
    }
  };

  const handleDescriptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setDescription(value);
    validate('description', value);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!file || !description || Object.keys(errors).length > 0) {
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', description);

    try {
      const response = await fetch('/api/documents', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to upload document');
      }

      const data = await response.json();
      onSuccess(data.documentId);

      // Reset form
      setFile(null);
      setDescription('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', maxWidth: 600 }}>
      <input
        type="file"
        accept=".pdf,.docx"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: 'none' }}
        aria-label="Choose file"
      />
      <Button
        variant="outlined"
        component="label"
        fullWidth
        onClick={() => fileInputRef.current?.click()}
        sx={{ mb: 2 }}
      >
        {file ? file.name : 'Choose File'}
      </Button>

      <TextField
        fullWidth
        label="Description"
        multiline
        rows={4}
        value={description}
        onChange={handleDescriptionChange}
        error={!!errors.description}
        helperText={errors.description || 'Describe the document content'}
        sx={{ mb: 2 }}
      />

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Button
        type="submit"
        variant="contained"
        fullWidth
        disabled={!file || !description || isUploading || Object.keys(errors).length > 0}
      >
        {isUploading ? <CircularProgress size={24} /> : 'Upload'}
      </Button>
    </Box>
  );
};

export default withErrorHandling(DocumentUploadForm); 