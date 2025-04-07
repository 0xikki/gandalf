import React, { ComponentType, useState, useCallback } from 'react';
import { Alert, Snackbar, AlertColor } from '@mui/material';

export interface ErrorDetails {
  message: string;
  code?: string | number;
  severity?: AlertColor;
  timestamp?: string;
  stack?: string;
}

export interface WithErrorHandlingProps {
  onError?: (error: ErrorDetails) => void;
}

export interface ErrorHandlingOptions {
  autoHideDuration?: number;
  defaultSeverity?: AlertColor;
  position?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'center' | 'right';
  };
  customFallback?: React.ReactNode;
  trackErrors?: boolean;
}

const defaultOptions: ErrorHandlingOptions = {
  autoHideDuration: 6000,
  defaultSeverity: 'error',
  position: {
    vertical: 'bottom',
    horizontal: 'center',
  },
  trackErrors: true,
};

export const withErrorHandling = <P extends object>(
  WrappedComponent: ComponentType<P>,
  options: ErrorHandlingOptions = defaultOptions
) => {
  return function WithErrorHandlingComponent(
    props: Omit<P, keyof WithErrorHandlingProps>
  ) {
    const [error, setError] = useState<ErrorDetails | null>(null);
    const [showError, setShowError] = useState(false);

    const {
      autoHideDuration,
      defaultSeverity,
      position,
      customFallback,
      trackErrors,
    } = { ...defaultOptions, ...options };

    const handleError = useCallback((error: Error | ErrorDetails) => {
      const errorDetails: ErrorDetails = {
        ...(error as ErrorDetails),
        message: error.message || 'An unexpected error occurred',
        severity: (error as ErrorDetails).severity || defaultSeverity,
        timestamp: new Date().toISOString(),
        stack: error.stack,
      };

      setError(errorDetails);
      setShowError(true);

      // Track errors if enabled
      if (trackErrors) {
        console.error('[Error Tracking]', {
          ...errorDetails,
          component: WrappedComponent.displayName || WrappedComponent.name,
          timestamp: errorDetails.timestamp,
        });

        // Here you could integrate with error tracking services like Sentry
        // if (window.Sentry) {
        //   window.Sentry.captureException(error);
        // }
      }
    }, [defaultSeverity, trackErrors]);

    const handleCloseError = useCallback(
      (event?: React.SyntheticEvent | Event, reason?: string) => {
        if (reason === 'clickaway') {
          return;
        }
        setShowError(false);
      },
      []
    );

    const handleExited = useCallback(() => {
      setError(null);
    }, []);

    if (error && customFallback) {
      return customFallback;
    }

    return (
      <>
        <WrappedComponent
          {...(props as P)}
          onError={handleError}
        />
        <Snackbar
          open={showError}
          autoHideDuration={autoHideDuration}
          onClose={handleCloseError}
          anchorOrigin={position}
          TransitionProps={{ onExited: handleExited }}
        >
          <Alert
            onClose={handleCloseError}
            severity={error?.severity || defaultSeverity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {error?.message || 'An error occurred'}
            {error?.code && ` (Code: ${error.code})`}
          </Alert>
        </Snackbar>
      </>
    );
  };
}; 