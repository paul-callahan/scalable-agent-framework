import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import NodeNameInput from '../NodeNameInput';

// Mock the validation utility
vi.mock('../../../utils/clientValidation', () => ({
  ClientValidation: {
    validateNodeName: vi.fn()
  }
}));

import { ClientValidation } from '../../../utils/clientValidation';

describe('NodeNameInput', () => {
  const mockOnChange = vi.fn();
  const mockOnValidationChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (ClientValidation.validateNodeName as any).mockReturnValue({
      valid: true,
      errors: [],
      warnings: []
    });
  });

  it('should render input field with label', () => {
    render(
      <NodeNameInput
        value=""
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
        label="Node Name"
      />
    );

    expect(screen.getByLabelText('Node Name')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('should call onChange when input value changes', () => {
    render(
      <NodeNameInput
        value=""
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test_name' } });

    expect(mockOnChange).toHaveBeenCalledWith('test_name');
  });

  it('should validate input and show validation result', async () => {
    (ClientValidation.validateNodeName as any).mockReturnValue({
      valid: false,
      errors: ['Name must be a valid Python identifier'],
      warnings: []
    });

    render(
      <NodeNameInput
        value="123invalid"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={['existing_name']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Name must be a valid Python identifier')).toBeInTheDocument();
    });

    expect(mockOnValidationChange).toHaveBeenCalledWith({
      valid: false,
      errors: ['Name must be a valid Python identifier'],
      warnings: []
    });
  });

  it('should show warnings when validation has warnings', async () => {
    (ClientValidation.validateNodeName as any).mockReturnValue({
      valid: true,
      errors: [],
      warnings: ['Names starting with underscore are typically private']
    });

    render(
      <NodeNameInput
        value="_private_name"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Names starting with underscore are typically private')).toBeInTheDocument();
    });
  });

  it('should show success state for valid names', async () => {
    (ClientValidation.validateNodeName as any).mockReturnValue({
      valid: true,
      errors: [],
      warnings: []
    });

    render(
      <NodeNameInput
        value="valid_name"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('valid');
  });

  it('should show error state for invalid names', async () => {
    (ClientValidation.validateNodeName as any).mockReturnValue({
      valid: false,
      errors: ['Invalid name'],
      warnings: []
    });

    render(
      <NodeNameInput
        value="invalid name"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('invalid');
  });

  it('should debounce validation calls', async () => {
    const { rerender } = render(
      <NodeNameInput
        value=""
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    // Rapidly change the value multiple times
    rerender(
      <NodeNameInput
        value="a"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    rerender(
      <NodeNameInput
        value="ab"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    rerender(
      <NodeNameInput
        value="abc"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    // Wait for debounce
    await waitFor(() => {
      expect(ClientValidation.validateNodeName).toHaveBeenCalledTimes(1);
    }, { timeout: 600 });
  });

  it('should handle empty value', () => {
    render(
      <NodeNameInput
        value=""
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    const input = screen.getByRole('textbox');
    expect(input.value).toBe('');
  });

  it('should exclude current name from uniqueness check', async () => {
    render(
      <NodeNameInput
        value="current_name"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={['current_name', 'other_name']}
        currentName="current_name"
      />
    );

    await waitFor(() => {
      expect(ClientValidation.validateNodeName).toHaveBeenCalledWith(
        'current_name',
        ['current_name', 'other_name'],
        'current_name'
      );
    });
  });

  it('should show placeholder text', () => {
    render(
      <NodeNameInput
        value=""
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
        placeholder="Enter node name..."
      />
    );

    expect(screen.getByPlaceholderText('Enter node name...')).toBeInTheDocument();
  });

  it('should handle disabled state', () => {
    render(
      <NodeNameInput
        value="test"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
        disabled={true}
      />
    );

    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
  });

  it('should show multiple errors', async () => {
    (ClientValidation.validateNodeName as any).mockReturnValue({
      valid: false,
      errors: ['Name must be a valid Python identifier', 'Name already exists'],
      warnings: []
    });

    render(
      <NodeNameInput
        value="123duplicate"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={['123duplicate']}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Name must be a valid Python identifier')).toBeInTheDocument();
      expect(screen.getByText('Name already exists')).toBeInTheDocument();
    });
  });

  it('should handle focus and blur events', () => {
    render(
      <NodeNameInput
        value="test"
        onChange={mockOnChange}
        onValidationChange={mockOnValidationChange}
        existingNames={[]}
      />
    );

    const input = screen.getByRole('textbox');
    
    fireEvent.focus(input);
    expect(input).toHaveClass('focused');
    
    fireEvent.blur(input);
    expect(input).not.toHaveClass('focused');
  });
});