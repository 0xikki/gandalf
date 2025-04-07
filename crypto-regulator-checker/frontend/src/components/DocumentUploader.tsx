import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { uploadDocument, getAnalysisResults } from '../services/api';

const DocumentUploader: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setAnalyzing(true);
      setError(null);
      
      // Upload the document with authentication
      const documentId = await uploadDocument(file, token);
      
      // Get analysis results
      const results = await getAnalysisResults(documentId, token);
      
      // Navigate to results page with the analysis data
      navigate('/results', { state: { results } });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 4,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        maxWidth: 600,
        mx: 'auto',
      }}
    >
      <Typography variant="h5" component="h2" gutterBottom>
        Upload Document for Analysis
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload a document to check for regulatory compliance
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3, width: '100%' }}>
          {error}
        </Alert>
      )}

      <Box sx={{ position: 'relative' }}>
        <Button
          variant="contained"
          component="label"
          disabled={analyzing}
          sx={{ minWidth: 200 }}
        >
          {analyzing ? 'Analyzing...' : 'Choose File'}
          <input
            type="file"
            hidden
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.txt"
          />
        </Button>
        {analyzing && (
          <CircularProgress
            size={24}
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              marginTop: '-12px',
              marginLeft: '-12px',
            }}
          />
        )}
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Supported formats: PDF, DOC, DOCX, TXT
      </Typography>
    </Paper>
  );
};

export default DocumentUploader; 