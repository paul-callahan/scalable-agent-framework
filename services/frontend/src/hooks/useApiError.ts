import { useCallback } from 'react';
import { useError } from '../context/ErrorContext';
import {
  NetworkError,
  ValidationError,
  TenantAccessError,
  FileProcessingError,
} from '../types/errors';

export const useApiError = () => {
  const { showError, showWarning } = useError();

  const handleError = useCallback((error: Error, context?: string) => {
    console.error('API Error:', error, context);

    if (error instanceof NetworkError) {
      showError(error.message, {
        duration: 8000,
        retryAction: {
          label: 'Refresh Page',
          action: () => {
            window.location.reload();
          },
        },
      });
    } else if (error instanceof ValidationError) {
      const message = error.errors.length > 0 
        ? `Validation failed: ${error.errors.join(', ')}`
        : error.message;
      showWarning(message, { duration: 6000 });
    } else if (error instanceof TenantAccessError) {
      showError(error.message, { duration: 10000 });
    } else if (error instanceof FileProcessingError) {
      const message = error.fileName 
        ? `File processing error in ${error.fileName}: ${error.message}`
        : error.message;
      showError(message, { duration: 6000 });
    } else {
      // Generic error
      const contextMessage = context ? `${context}: ` : '';
      showError(`${contextMessage}${error.message}`, { duration: 5000 });
    }
  }, [showError, showWarning]);

  const handleAsyncError = useCallback(async <T>(
    asyncFn: () => Promise<T>,
    context?: string
  ): Promise<T | null> => {
    try {
      return await asyncFn();
    } catch (error) {
      const err = error as Error;
      
      // Always handle errors the same way - no automatic retry actions
      // to prevent infinite loops
      handleError(err, context);
      
      return null;
    }
  }, [handleError]);

  return {
    handleError,
    handleAsyncError,
  };
};