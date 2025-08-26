import React from 'react';
import type { ValidationResult } from '../../types';
import './ValidationFeedback.css';

export interface ValidationFeedbackProps {
  validationResult?: ValidationResult | null;
  className?: string;
  showWarnings?: boolean;
}

const ValidationFeedback: React.FC<ValidationFeedbackProps> = ({
  validationResult,
  className = '',
  showWarnings = true
}) => {
  if (!validationResult) {
    return null;
  }

  const hasErrors = validationResult.errors && validationResult.errors.length > 0;
  const hasWarnings = validationResult.warnings && validationResult.warnings.length > 0;

  if (!hasErrors && (!showWarnings || !hasWarnings)) {
    return null;
  }

  return (
    <div className={`validation-feedback ${className}`}>
      {hasErrors && (
        <div className="validation-errors">
          <div className="validation-section-header">
            <span className="validation-icon error-icon">⚠️</span>
            <span className="validation-title">Validation Errors</span>
          </div>
          <ul className="validation-list">
            {validationResult.errors.map((error, index) => (
              <li key={index} className="validation-item error-item">
                {error}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {showWarnings && hasWarnings && (
        <div className="validation-warnings">
          <div className="validation-section-header">
            <span className="validation-icon warning-icon">⚡</span>
            <span className="validation-title">Warnings</span>
          </div>
          <ul className="validation-list">
            {validationResult.warnings.map((warning, index) => (
              <li key={index} className="validation-item warning-item">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ValidationFeedback;