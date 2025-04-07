export interface AnalysisResult {
  status: 'success' | 'warning' | 'error';
  message: string;
  details: string[];
  regulations: {
    id: string;
    title: string;
    relevance: number;
    description: string;
  }[];
}

export interface DocumentUploaderProps {
  onFileSelect: (file: File) => Promise<void>;
  isAnalyzing: boolean;
  error: string | null;
} 