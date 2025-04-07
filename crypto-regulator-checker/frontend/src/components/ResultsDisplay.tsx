import React from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { styled } from '@mui/material/styles';

// Types
interface AnalysisResult {
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

interface ResultsDisplayProps {
  isLoading?: boolean;
  error?: string;
  results?: AnalysisResult;
}

// Styled components
const ResultContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  maxWidth: 800,
  margin: '0 auto',
  marginTop: theme.spacing(4),
}));

const RegulationItem = styled(ListItem)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
}));

const getStatusColor = (status: AnalysisResult['status']) => {
  switch (status) {
    case 'compliant':
      return 'success';
    case 'non-compliant':
      return 'error';
    case 'warning':
      return 'warning';
    default:
      return 'default';
  }
};

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  isLoading = false,
  error,
  results,
}) => {
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box mt={4}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!results) {
    return null;
  }

  return (
    <ResultContainer elevation={3}>
      <Box mb={3}>
        <Typography variant="h5" gutterBottom>
          Analysis Results
        </Typography>
        <Chip
          label={results.status.toUpperCase()}
          color={getStatusColor(results.status)}
          sx={{ mb: 2 }}
        />
        <Typography variant="body1">{results.message}</Typography>
      </Box>

      {results.details.length > 0 && (
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Key Findings
          </Typography>
          <List>
            {results.details.map((detail, index) => (
              <ListItem key={index}>
                <ListItemText primary={detail} />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {results.regulations.length > 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Relevant Regulations
          </Typography>
          <List>
            {results.regulations.map((regulation) => (
              <RegulationItem key={regulation.id}>
                <ListItemText
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle1">{regulation.title}</Typography>
                      <Chip
                        label={`${Math.round(regulation.relevance * 100)}% Match`}
                        size="small"
                        color="primary"
                      />
                    </Box>
                  }
                  secondary={regulation.description}
                />
              </RegulationItem>
            ))}
          </List>
        </Box>
      )}
    </ResultContainer>
  );
};

export default ResultsDisplay; 