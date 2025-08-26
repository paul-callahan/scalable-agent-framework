import React from 'react';
import { render, screen } from '@testing-library/react';
import ValidationStatusBar from '../ValidationStatusBar';
import type { ValidationResult } from '../../../types';

describe('ValidationStatusBar', () => {
  it('should show valid status when validation passes', () => {
    const validResult: ValidationResult = {
      valid: true,
      errors: [],
      warnings: []
    };

    render(<ValidationStatusBar validationResult={validResult} />);

    expect(screen.getByText('Graph is valid')).toBeInTheDocument();
    expect(screen.getByTestId('validation-status')).toHaveClass('valid');
  });

  it('should show error status when validation fails', () => {
    const invalidResult: ValidationResult = {
      valid: false,
      errors: ['Node names must be unique', 'Tasks must have exactly one upstream plan'],
      warnings: []
    };

    render(<ValidationStatusBar validationResult={invalidResult} />);

    expect(screen.getByText('2 validation errors')).toBeInTheDocument();
    expect(screen.getByTestId('validation-status')).toHaveClass('invalid');
  });

  it('should show warning status when there are warnings but no errors', () => {
    const warningResult: ValidationResult = {
      valid: true,
      errors: [],
      warnings: ['Node "orphan_plan" is not connected to any tasks']
    };

    render(<ValidationStatusBar validationResult={warningResult} />);

    expect(screen.getByText('1 warning')).toBeInTheDocument();
    expect(screen.getByTestId('validation-status')).toHaveClass('warning');
  });

  it('should show both errors and warnings', () => {
    const mixedResult: ValidationResult = {
      valid: false,
      errors: ['Node names must be unique'],
      warnings: ['Node "orphan_plan" is not connected to any tasks']
    };

    render(<ValidationStatusBar validationResult={mixedResult} />);

    expect(screen.getByText('1 error, 1 warning')).toBeInTheDocument();
    expect(screen.getByTestId('validation-status')).toHaveClass('invalid');
  });

  it('should display detailed error messages when expanded', () => {
    const invalidResult: ValidationResult = {
      valid: false,
      errors: ['Node names must be unique', 'Tasks must have exactly one upstream plan'],
      warnings: ['Node "orphan_plan" is not connected to any tasks']
    };

    render(<ValidationStatusBar validationResult={invalidResult} expanded={true} />);

    expect(screen.getByText('Node names must be unique')).toBeInTheDocument();
    expect(screen.getByText('Tasks must have exactly one upstream plan')).toBeInTheDocument();
    expect(screen.getByText('Node "orphan_plan" is not connected to any tasks')).toBeInTheDocument();
  });

  it('should handle empty validation result', () => {
    render(<ValidationStatusBar validationResult={null} />);

    expect(screen.getByText('No validation performed')).toBeInTheDocument();
    expect(screen.getByTestId('validation-status')).toHaveClass('unknown');
  });

  it('should show loading state during validation', () => {
    render(<ValidationStatusBar validationResult={null} loading={true} />);

    expect(screen.getByText('Validating...')).toBeInTheDocument();
    expect(screen.getByTestId('validation-status')).toHaveClass('loading');
  });

  it('should show correct icons for different states', () => {
    const validResult: ValidationResult = {
      valid: true,
      errors: [],
      warnings: []
    };

    const { rerender } = render(<ValidationStatusBar validationResult={validResult} />);
    expect(screen.getByTestId('validation-icon')).toHaveClass('success-icon');

    const invalidResult: ValidationResult = {
      valid: false,
      errors: ['Error'],
      warnings: []
    };

    rerender(<ValidationStatusBar validationResult={invalidResult} />);
    expect(screen.getByTestId('validation-icon')).toHaveClass('error-icon');

    const warningResult: ValidationResult = {
      valid: true,
      errors: [],
      warnings: ['Warning']
    };

    rerender(<ValidationStatusBar validationResult={warningResult} />);
    expect(screen.getByTestId('validation-icon')).toHaveClass('warning-icon');
  });

  it('should handle multiple errors and warnings correctly', () => {
    const complexResult: ValidationResult = {
      valid: false,
      errors: ['Error 1', 'Error 2', 'Error 3'],
      warnings: ['Warning 1', 'Warning 2']
    };

    render(<ValidationStatusBar validationResult={complexResult} />);

    expect(screen.getByText('3 errors, 2 warnings')).toBeInTheDocument();
  });

  it('should use singular form for single error/warning', () => {
    const singleResult: ValidationResult = {
      valid: false,
      errors: ['Single error'],
      warnings: ['Single warning']
    };

    render(<ValidationStatusBar validationResult={singleResult} />);

    expect(screen.getByText('1 error, 1 warning')).toBeInTheDocument();
  });
});