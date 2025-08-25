import { useState, useEffect, useCallback } from 'react';
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

  const loadGraphs = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    const result = await handleAsyncError(
      () => executeWithRetry(
        () => graphApi.listGraphs(state.tenantId),
        'loadGraphs'
      ),
      'Failed to load graphs'
    );
    
    if (result) {
      setGraphs(result);
    }
    
    dispatch({ type: 'SET_LOADING', payload: false });
  }, [state.tenantId, dispatch, handleAsyncError, executeWithRetry]);

  const loadGraph = async (graphId: string): Promise<AgentGraphDto> => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    const result = await handleAsyncError(
      () => executeWithRetry(
        () => graphApi.getGraph(graphId, state.tenantId),
        `loadGraph-${graphId}`
      ),
      'Failed to load graph'
    );
    
    if (result) {
      dispatch({ type: 'SET_CURRENT_GRAPH', payload: result });
      dispatch({ type: 'SET_LOADING', payload: false });
      return result;
    }
    
    dispatch({ type: 'SET_LOADING', payload: false });
    throw new Error('Failed to load graph');
  };

  const createGraph = async (request: CreateGraphRequest): Promise<AgentGraphDto> => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
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
      dispatch({ type: 'SET_LOADING', payload: false });
      return result;
    }
    
    dispatch({ type: 'SET_LOADING', payload: false });
    throw new Error('Failed to create graph');
  };

  const updateGraph = async (graphId: string, graph: AgentGraphDto): Promise<AgentGraphDto> => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    const result = await handleAsyncError(
      () => executeWithRetry(
        () => graphApi.updateGraph(graphId, graph),
        `updateGraph-${graphId}`
      ),
      'Failed to update graph'
    );
    
    if (result) {
      dispatch({ type: 'SET_CURRENT_GRAPH', payload: result });
      dispatch({ type: 'SET_LOADING', payload: false });
      return result;
    }
    
    dispatch({ type: 'SET_LOADING', payload: false });
    throw new Error('Failed to update graph');
  };

  const deleteGraph = async (graphId: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
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
    
    dispatch({ type: 'SET_LOADING', payload: false });
  };

  const submitForExecution = async (graphId: string): Promise<ExecutionResponse> => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    const result = await handleAsyncError(
      () => executeWithRetry(
        () => graphApi.submitForExecution(graphId, state.tenantId),
        `submitForExecution-${graphId}`
      ),
      'Failed to submit for execution'
    );
    
    if (result) {
      await loadGraphs(); // Refresh to get updated status
      dispatch({ type: 'SET_LOADING', payload: false });
      return result;
    }
    
    dispatch({ type: 'SET_LOADING', payload: false });
    throw new Error('Failed to submit for execution');
  };

  useEffect(() => {
    loadGraphs();
  }, [loadGraphs]);

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