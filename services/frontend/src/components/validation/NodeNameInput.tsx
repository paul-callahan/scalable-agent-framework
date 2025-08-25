import React, { useState, useEffect, useCallback } from 'react';
import { useValidation } from '../../hooks/useValidation';
import ValidationFeedback from './ValidationFeedback';
import type { ValidationResult } from '../../types';
import './NodeNameInput.css';

export interface NodeNameInputProps {
  value: string;
  onChange: (value: string) => void;
  onValidationChange?: (isValid: boolean, result: ValidationResult) => void;
  graphId: string;
  existingNodeNames?: string[];
  excludeNodeId?: string;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  className?: string;
  showValidationFeedback?: boolean;
}

const NodeNameInput: React.FC<NodeNameInputProps> = ({
  value,
  onChange,
  onValidationChange,
  existingNodeNames = [],
  excludeNodeId,
  placeholder = 'Enter node name...',
  disabled = false,
  autoFocus = false,
  className = '',
  showValidationFeedback = true
}) => {
  const { validateNodeNameSync } = useValidation();
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

  const performValidation = useCallback((nodeName: string) => {
    if (!nodeName.trim()) {
      const emptyResult: ValidationResult = {
        valid: true,
        errors: [],
        warnings: []
      };
      setValidationResult(emptyResult);
      onValidationChange?.(true, emptyResult);
      return;
    }

    // Use synchronous client-side validation for immediate feedback
    const result = validateNodeNameSync(
      nodeName,
      existingNodeNames,
      excludeNodeId
    );
    
    setValidationResult(result);
    onValidationChange?.(result.valid, result);
  }, [validateNodeNameSync, existingNodeNames, excludeNodeId, onValidationChange]);

  // Immediate validation (no debouncing needed for client-side validation)
  useEffect(() => {
    performValidation(value);
  }, [value, performValidation]);



  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const getInputClassName = () => {
    let inputClass = 'node-name-input';
    
    if (className) {
      inputClass += ` ${className}`;
    }
    
    if (validationResult && value.trim()) {
      if (!validationResult.valid) {
        inputClass += ' error';
      } else if (validationResult.warnings && validationResult.warnings.length > 0) {
        inputClass += ' warning';
      } else {
        inputClass += ' valid';
      }
    }
    
    return inputClass;
  };

  return (
    <div className="node-name-input-container">
      <div className="input-wrapper">
        <input
          type="text"
          value={value}
          onChange={handleInputChange}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          className={getInputClassName()}
        />
        {validationResult && value.trim() && (
          <div className="validation-indicator">
            {validationResult.valid ? (
              validationResult.warnings && validationResult.warnings.length > 0 ? (
                <span className="warning-indicator" title="Has warnings">⚡</span>
              ) : (
                <span className="success-indicator" title="Valid">✓</span>
              )
            ) : (
              <span className="error-indicator" title="Has errors">⚠️</span>
            )}
          </div>
        )}
      </div>
      
      {showValidationFeedback && validationResult && value.trim() && (
        <ValidationFeedback
          validationResult={validationResult}
          className="compact"
          showWarnings={true}
        />
      )}
    </div>
  );
};

export default NodeNameInput;