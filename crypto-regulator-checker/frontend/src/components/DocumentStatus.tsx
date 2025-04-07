import React, { useEffect, useState } from 'react';
import { Box, Typography, LinearProgress, Paper } from '@mui/material';
import { formatDistanceToNow } from 'date-fns';
import { useDocumentWebSocket } from '../hooks/useDocumentWebSocket';
import { withErrorHandling } from '../hoc/withErrorHandling';

interface DocumentStatusProps {
  documentId: string;
}

interface DocumentStatusData {
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress?: number;
  message?: string;
  lastUpdated?: string;
}

export const DocumentStatus: React.FC<DocumentStatusProps> = ({ documentId }) => {
  const [status, setStatus] = useState<DocumentStatusData>({
    status: 'pending',
    message: 'Loading document status...'
  });

  const { data, error } = useDocumentWebSocket(documentId);

  useEffect(() => {
    if (data) {
      setStatus(data);
    }
  }, [data]);

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2, bgcolor: '#fff3f3' }}>
        <Typography color="error">
          Failed to connect: {error.message}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Document Status
        </Typography>
        <Typography
          variant="subtitle1"
          sx={{
            color: status.status === 'error' ? 'error.main' :
                  status.status === 'completed' ? 'success.main' :
                  'text.primary'
          }}
        >
          {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
        </Typography>
      </Box>

      {status.progress !== undefined && status.status === 'processing' && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress
            variant="determinate"
            value={status.progress}
            sx={{ mb: 1 }}
          />
          <Typography variant="body2" color="text.secondary">
            {status.progress}% Complete
          </Typography>
        </Box>
      )}

      {status.message && (
        <Typography variant="body1" sx={{ mb: 2 }}>
          {status.message}
        </Typography>
      )}

      {status.lastUpdated && (
        <Typography variant="caption" color="text.secondary">
          Last updated {formatDistanceToNow(new Date(status.lastUpdated))} ago
        </Typography>
      )}
    </Paper>
  );
};

export default withErrorHandling(DocumentStatus); 