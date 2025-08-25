import React, { useState, useCallback } from 'react';
import ValidationFeedback from './ValidationFeedback';
import type { ValidationResult } from '../../types';
import './ValidationStatusBar.css';

export interface ValidationStatusBarProps {
  validationResult?: ValidationResult | null;
  isValidating?: boolean;
  onRefreshValidation?: () => void;
  className?: string;
}

const ValidationStatusBar: React.FC<ValidationStatusBarProps> = ({
  validationResult,
  isValidating = false,
  onRefreshValidation,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  const handleRefresh = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onRefreshValidation?.();
  }, [onRefreshValidation]);

  if (!validationResult && !isValidating) {
    return null;
  }

  const hasErrors = validationResult?.errors && validationResult.errors.length > 0;
  const hasWarnings = validationResult?.warnings && validationResult.warnings.length > 0;
  const isValid = validationResult?.valid ?? false;

  const getStatusIcon = () => {
    if (isValidating) {
      return <div className="validation-spinner"><div className="spinner"></div></div>;
    }
    
    if (hasErrors) {
      return <span className="status-icon error">⚠️</span>;
    }
    
    if (hasWarnings) {
      return <span className="status-icon warning">⚡</span>;
    }
    
    if (isValid) {
      return <span className="status-icon success">✓</span>;
    }
    
    return <span className="status-icon unknown">?</span>;
  };

  const getStatusText = () => {
    if (isValidating) {
      return 'Validating graph...';
    }
    
    if (hasErrors) {
      const errorCount = validationResult?.errors?.length || 0;
      const warningCount = validationResult?.warnings?.length || 0;
      return `${errorCount} error${errorCount !== 1 ? 's' : ''}${warningCount > 0 ? `, ${warningCount} warning${warningCount !== 1 ? 's' : ''}` : ''}`;
    }
    
    if (hasWarnings) {
      const warningCount = validationResult?.warnings?.length || 0;
      return `${warningCount} warning${warningCount !== 1 ? 's' : ''}`;
    }
    
    if (isValid) {
      return 'Graph is valid';
    }
    
    return 'Validation status unknown';
  };

  const getStatusClassName = () => {
    let statusClass = 'validation-status-bar';
    
    if (className) {
      statusClass += ` ${className}`;
    }
    
    if (isValidating) {
      statusClass += ' validating';
    } else if (hasErrors) {
      statusClass += ' error';
    } else if (hasWarnings) {
      statusClass += ' warning';
    } else if (isValid) {
      statusClass += ' success';
    }
    
    if (isExpanded) {
      statusClass += ' expanded';
    }
    
    return statusClass;
  };

  return (
    <div className={getStatusClassName()}>
      <div className="status-header" onClick={toggleExpanded}>
        <div className="status-info">
          {getStatusIcon()}
          <span className="status-text">{getStatusText()}</span>
        </div>
        
        <div className="status-actions">
          {onRefreshValidation && (
            <button
              className="refresh-button"
              onClick={handleRefresh}
              disabled={isValidating}
              title="Refresh validation"
            >
              🔄
            </button>
          )}
          
          {(hasErrors || hasWarnings) && (
            <button
              className="expand-button"
              onClick={toggleExpanded}
              title={isExpanded ? 'Hide details' : 'Show details'}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
        </div>
      </div>
      
      {isExpanded && validationResult && (
        <div className="status-details">
          <ValidationFeedback
            validationResult={validationResult}
            showWarnings={true}
          />
        </div>
      )}
    </div>
  );
};

export default ValidationStatusBar;