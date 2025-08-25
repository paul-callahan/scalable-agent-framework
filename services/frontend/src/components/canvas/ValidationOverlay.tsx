import React from 'react';
import ValidationFeedback from '../validation/ValidationFeedback';
import type { ValidationResult } from '../../types';
import './ValidationOverlay.css';

export interface ValidationOverlayProps {
  validationResult?: ValidationResult | null;
  isVisible: boolean;
  position?: { x: number; y: number };
  className?: string;
}

const ValidationOverlay: React.FC<ValidationOverlayProps> = ({
  validationResult,
  isVisible,
  position = { x: 20, y: 20 },
  className = ''
}) => {
  if (!isVisible || !validationResult || (
    (!validationResult.errors || validationResult.errors.length === 0) &&
    (!validationResult.warnings || validationResult.warnings.length === 0)
  )) {
    return null;
  }

  const overlayStyle: React.CSSProperties = {
    left: position.x,
    top: position.y,
  };

  return (
    <div 
      className={`validation-overlay ${className}`}
      style={overlayStyle}
    >
      <ValidationFeedback
        validationResult={validationResult}
        className="tooltip"
        showWarnings={true}
      />
    </div>
  );
};

export default ValidationOverlay;