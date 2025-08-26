import { useCallback, useState } from 'react';
import { validationApi } from '../api/client';
import { ClientValidation } from '../utils/clientValidation';
import type { AgentGraphDto, ValidationResult, NodeNameValidationRequest } from '../types';

export interface ValidationState {
  isValidating: boolean;
  lastValidationResult: ValidationResult | null;
  validationErrors: string[];
  validationWarnings: string[];
}

export function useValidation() {
  const [validationState, setValidationState] = useState<ValidationState>({
    isValidating: false,
    lastValidationResult: null,
    validationErrors: [],
    validationWarnings: []
  });

  const validateGraph = useCallback(async (graph: AgentGraphDto, useServerValidation = false): Promise<ValidationResult> => {
    setValidationState(prev => ({ ...prev, isValidating: true }));
    
    try {
      let result: ValidationResult;
      
      if (useServerValidation) {
        // Use server-side validation for complex business rules or database checks
        result = await validationApi.validateGraph(graph);
      } else {
        // Use client-side validation for immediate feedback
        result = ClientValidation.validateGraph(graph);
      }
      
      setValidationState({
        isValidating: false,
        lastValidationResult: result,
        validationErrors: result.errors || [],
        validationWarnings: result.warnings || []
      });
      
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Validation failed';
      const errorResult: ValidationResult = {
        valid: false,
        errors: [errorMessage],
        warnings: []
      };
      
      setValidationState({
        isValidating: false,
        lastValidationResult: errorResult,
        validationErrors: [errorMessage],
        validationWarnings: []
      });
      
      return errorResult;
    }
  }, []);

  const validateNodeName = useCallback(async (
    nodeName: string,
    graphId: string,
    existingNodeNames?: string[],
    excludeNodeId?: string,
    useServerValidation = false
  ): Promise<ValidationResult> => {
    try {
      if (useServerValidation) {
        // Use server-side validation for database uniqueness checks
        const request: NodeNameValidationRequest = {
          nodeName: nodeName.trim(),
          graphId,
          existingNodeNames,
          excludeNodeId
        };
        
        return await validationApi.validateNodeName(request);
      } else {
        // Use client-side validation for immediate feedback
        return ClientValidation.validateNodeName(
          nodeName,
          existingNodeNames || [],
          excludeNodeId
        );
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Node name validation failed';
      return {
        valid: false,
        errors: [errorMessage],
        warnings: []
      };
    }
  }, []);

  const clearValidation = useCallback(() => {
    setValidationState({
      isValidating: false,
      lastValidationResult: null,
      validationErrors: [],
      validationWarnings: []
    });
  }, []);

  // Immediate client-side validation without state updates
  const validateNodeNameSync = useCallback((
    nodeName: string,
    existingNodeNames?: string[],
    excludeNodeId?: string
  ): ValidationResult => {
    return ClientValidation.validateNodeName(
      nodeName,
      existingNodeNames || [],
      excludeNodeId
    );
  }, []);

  const validateGraphSync = useCallback((graph: AgentGraphDto): ValidationResult => {
    return ClientValidation.validateGraph(graph);
  }, []);

  const hasValidationErrors = validationState.validationErrors.length > 0;
  const hasValidationWarnings = validationState.validationWarnings.length > 0;

  return {
    validationState,
    validateGraph,
    validateNodeName,
    validateNodeNameSync,
    validateGraphSync,
    clearValidation,
    hasValidationErrors,
    hasValidationWarnings,
    isValidating: validationState.isValidating
  };
}