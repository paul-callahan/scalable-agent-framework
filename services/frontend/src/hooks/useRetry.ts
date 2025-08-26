import { useState, useCallback, useRef } from 'react';
import { NetworkError } from '../types/errors';

interface RetryConfig {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryableErrors?: string[];
}

interface RetryState {
  attempts: number;
  isRetrying: boolean;
  lastError: Error | null;
}

const DEFAULT_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  initialDelay: 2000, // 2 seconds - increased from 1 second
  maxDelay: 60000, // 60 seconds - increased from 30 seconds
  backoffMultiplier: 3, // Increased from 2 for more aggressive backoff
  retryableErrors: ['NetworkError', 'TimeoutError', 'ConnectionError'],
};

// Utility function to delay execution
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Check if error is retryable
const isRetryableError = (error: Error, retryableErrors: string[]): boolean => {
  // Always retry NetworkErrors
  if (error instanceof NetworkError) {
    return true;
  }
  
  return retryableErrors.some(retryableType => 
    error.constructor.name === retryableType || 
    error.name === retryableType ||
    error.message.toLowerCase().includes(retryableType.toLowerCase())
  );
};

export const useRetry = (config: RetryConfig = {}) => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  const [retryState, setRetryState] = useState<RetryState>({
    attempts: 0,
    isRetrying: false,
    lastError: null,
  });
  
  // Use ref to track ongoing retry operations and prevent duplicates
  const ongoingRetries = useRef(new Set<string>());

  const executeWithRetry = useCallback(async <T>(
    operation: () => Promise<T>,
    operationId?: string
  ): Promise<T> => {
    const id = operationId || Math.random().toString(36);
    
    // Prevent duplicate retries for the same operation
    if (ongoingRetries.current.has(id)) {
      throw new Error('Operation already in progress');
    }

    ongoingRetries.current.add(id);
    
    try {
      setRetryState({ attempts: 0, isRetrying: false, lastError: null });
      
      for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
        try {
          const result = await operation();
          ongoingRetries.current.delete(id);
          setRetryState({ attempts: attempt, isRetrying: false, lastError: null });
          return result;
        } catch (error) {
          const err = error as Error;
          
          setRetryState({ 
            attempts: attempt + 1, 
            isRetrying: attempt < finalConfig.maxRetries, 
            lastError: err 
          });

          // Don't retry if it's the last attempt or error is not retryable
          if (attempt === finalConfig.maxRetries || 
              !isRetryableError(err, finalConfig.retryableErrors)) {
            ongoingRetries.current.delete(id);
            throw err;
          }

          // Calculate delay with exponential backoff
          const delayMs = Math.min(
            finalConfig.initialDelay * Math.pow(finalConfig.backoffMultiplier, attempt),
            finalConfig.maxDelay
          );

          console.log(`Retrying operation after ${delayMs}ms (attempt ${attempt + 1}/${finalConfig.maxRetries})`);
          await delay(delayMs);
        }
      }
    } catch (error) {
      ongoingRetries.current.delete(id);
      throw error;
    }
    
    // This should never be reached, but TypeScript needs it
    ongoingRetries.current.delete(id);
    throw new Error('Unexpected end of retry loop');
  }, [finalConfig]);

  const reset = useCallback(() => {
    setRetryState({ attempts: 0, isRetrying: false, lastError: null });
  }, []);

  return {
    executeWithRetry,
    retryState,
    reset,
  };
};
