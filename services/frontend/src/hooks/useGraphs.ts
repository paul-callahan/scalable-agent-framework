import { useState, useEffect, useCallback, useRef } from 'react';
import { graphApi } from '../api/client';
import type { AgentGraphSummary, AgentGraphDto, CreateGraphRequest, ExecutionResponse } from '../types';
import { useAppContext } from './useAppContext';
import { useApiError } from './useApiError';
import { useRetry } from './useRetry';

export function useGraphs() {
  const { state, dispatch } = useAppContext();
  const { handleAsyncError } = useApiError();
  const { executeWithRetry } = useRetry({
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    retryableErrors: ['NetworkError', 'TimeoutError', 'ConnectionError']
  });
  const [graphs, setGraphs] = useState<AgentGraphSummary[]>([]);
  
  // Use refs to prevent infinite loops and track loading state
  const isLoadingRef = useRef(false);
  const hasInitializedRef = useRef(false);
  const retryCountRef = useRef(0);
  const maxRetriesRef = useRef(5); // Maximum retries before giving up

  const loadGraphs = useCallback(async () => {
    // Prevent multiple simultaneous calls
    if (isLoadingRef.current) {
      return;
    }
    
    // Prevent infinite loops by checking retry count
    if (retryCountRef.current >= maxRetriesRef.current) {
      console.warn('Max retries reached for loadGraphs, giving up');
      return;
    }
    
    isLoadingRef.current = true;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    try {
      const result = await handleAsyncError(
        () => executeWithRetry(
          () => graphApi.listGraphs(state.tenantId),
          'loadGraphs'
        ),
        'Failed to load graphs'
      );
      
      if (result) {
        setGraphs(result);
        hasInitializedRef.current = true;
        retryCountRef.current = 0; // Reset retry count on success
      }
    } catch (error) {
      console.error('Error loading graphs:', error);
      retryCountRef.current++;
      
      // Don't show error toast for network issues to prevent spam
      if (error instanceof Error && !error.message.includes('Network')) {
        dispatch({ type: 'SET_ERROR', payload: error.message });
      }
      
      // Exponential backoff for retries
      if (retryCountRef.current < maxRetriesRef.current) {
        const delayMs = Math.min(1000 * Math.pow(2, retryCountRef.current - 1), 30000);
        console.log(`Retrying loadGraphs in ${delayMs}ms (attempt ${retryCountRef.current}/${maxRetriesRef.current})`);
        setTimeout(() => {
          isLoadingRef.current = false;
          loadGraphs();
        }, delayMs);
        return; // Don't set loading to false yet
      }
    } finally {
      // Always set loading to false when we're done (success or max retries reached)
      isLoadingRef.current = false;
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.tenantId, dispatch, handleAsyncError, executeWithRetry]);

  const loadGraph = useCallback(async (graphId: string): Promise<AgentGraphDto> => {
    if (isLoadingRef.current) {
      throw new Error('Operation already in progress');
    }
    
    isLoadingRef.current = true;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    try {
      const result = await handleAsyncError(
        () => executeWithRetry(
          () => graphApi.getGraph(graphId, state.tenantId),
          `loadGraph-${graphId}`
        ),
        'Failed to load graph'
      );
      
      if (result) {
        dispatch({ type: 'SET_CURRENT_GRAPH', payload: result });
        return result;
      }
      
      throw new Error('Failed to load graph');
    } finally {
      isLoadingRef.current = false;
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.tenantId, dispatch, handleAsyncError, executeWithRetry]);

  const createGraph = useCallback(async (request: CreateGraphRequest): Promise<AgentGraphDto> => {
    if (isLoadingRef.current) {
      throw new Error('Operation already in progress');
    }
    
    isLoadingRef.current = true;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    try {
      const result = await handleAsyncError(
        () => executeWithRetry(
          () => graphApi.createGraph(request),
          `createGraph-${request.name}`
        ),
        'Failed to create graph'
      );
      
      if (result) {
        dispatch({ type: 'SET_CURRENT_GRAPH', payload: result });
        await loadGraphs(); // Refresh the list
        return result;
      }
      
      throw new Error('Failed to create graph');
    } finally {
      isLoadingRef.current = false;
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [dispatch, handleAsyncError, executeWithRetry, loadGraphs]);

  const updateGraph = useCallback(async (graphId: string, graph: AgentGraphDto): Promise<AgentGraphDto> => {
    if (isLoadingRef.current) {
      throw new Error('Operation already in progress');
    }
    
    isLoadingRef.current = true;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    try {
      const result = await handleAsyncError(
        () => executeWithRetry(
          () => graphApi.updateGraph(graphId, graph),
          `updateGraph-${graphId}`
        ),
        'Failed to update graph'
      );
      
      if (result) {
        dispatch({ type: 'SET_CURRENT_GRAPH', payload: result });
        return result;
      }
      
      throw new Error('Failed to update graph');
    } finally {
      isLoadingRef.current = false;
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [dispatch, handleAsyncError, executeWithRetry]);

  const deleteGraph = useCallback(async (graphId: string) => {
    if (isLoadingRef.current) {
      throw new Error('Operation already in progress');
    }
    
    isLoadingRef.current = true;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    try {
      const result = await handleAsyncError(
        () => executeWithRetry(
          () => graphApi.deleteGraph(graphId, state.tenantId),
          `deleteGraph-${graphId}`
        ),
        'Failed to delete graph'
      );
      
      if (result !== null) {
        await loadGraphs(); // Refresh the list
      }
    } finally {
      isLoadingRef.current = false;
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.tenantId, dispatch, handleAsyncError, executeWithRetry, loadGraphs]);

  const submitForExecution = useCallback(async (graphId: string): Promise<ExecutionResponse> => {
    if (isLoadingRef.current) {
      throw new Error('Operation already in progress');
    }
    
    isLoadingRef.current = true;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    try {
      const result = await handleAsyncError(
        () => executeWithRetry(
          () => graphApi.submitForExecution(graphId, state.tenantId),
          `submitForExecution-${graphId}`
        ),
        'Failed to submit for execution'
      );
      
      if (result) {
        await loadGraphs(); // Refresh to get updated status
        return result;
      }
      
      throw new Error('Failed to submit for execution');
    } finally {
      isLoadingRef.current = false;
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.tenantId, dispatch, handleAsyncError, executeWithRetry, loadGraphs]);

  // Only load graphs once on mount, not on every render
  useEffect(() => {
    if (!hasInitializedRef.current) {
      loadGraphs();
    }
  }, []); // Empty dependency array - only run once

  return {
    graphs,
    loadGraphs,
    loadGraph,
    createGraph,
    updateGraph,
    deleteGraph,
    submitForExecution,
  };
}