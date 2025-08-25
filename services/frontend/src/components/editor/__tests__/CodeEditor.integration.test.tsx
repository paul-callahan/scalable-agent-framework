import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import CodeEditor from '../CodeEditor';
import type { ExecutorFile } from '../../../types';

// Mock the API client
const mockUpdatePlanFile = vi.fn();
const mockUpdateTaskFile = vi.fn();

vi.mock('../../../api/client', () => ({
  fileApi: {
    updatePlanFile: mockUpdatePlanFile,
    updateTaskFile: mockUpdateTaskFile,
  },
}));

// Mock CodeMirror
vi.mock('@uiw/react-codemirror', () => ({
  default: ({ value, onChange }: { value: string; onChange: (val: string) => void }) => (
    <textarea
      data-testid="codemirror-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

describe('CodeEditor Integration', () => {
  const mockPythonFile: ExecutorFile = {
    name: 'plan.py',
    contents: 'from agentic_common.pb import PlanInput, PlanResult\n\ndef plan(plan_input: PlanInput) -> PlanResult:\n    pass',
    creationDate: '2024-01-01T00:00:00Z',
    version: '1.0',
    updateDate: '2024-01-01T00:00:00Z',
  };

  const mockRequirementsFile: ExecutorFile = {
    name: 'requirements.txt',
    contents: '# Add your dependencies here\nrequests>=2.25.1',
    creationDate: '2024-01-01T00:00:00Z',
    version: '1.0',
    updateDate: '2024-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle Python file editing with syntax highlighting context', () => {
    render(<CodeEditor file={mockPythonFile} language="python" />);
    
    expect(screen.getByText('plan.py')).toBeInTheDocument();
    expect(screen.getByDisplayValue(/from agentic_common.pb import PlanInput/)).toBeInTheDocument();
  });

  it('should handle requirements.txt file editing with plaintext context', () => {
    render(<CodeEditor file={mockRequirementsFile} language="plaintext" />);
    
    expect(screen.getByText('requirements.txt')).toBeInTheDocument();
    expect(screen.getByDisplayValue(/# Add your dependencies here/)).toBeInTheDocument();
  });

  it('should track unsaved changes and enable save functionality', async () => {
    const mockOnSave = vi.fn();
    render(<CodeEditor file={mockPythonFile} onSave={mockOnSave} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    const saveButton = screen.getByText('Save');
    
    // Initially no unsaved changes
    expect(screen.queryByText('●')).not.toBeInTheDocument();
    expect(saveButton).toBeDisabled();
    
    // Make changes
    const newContent = 'from agentic_common.pb import PlanInput, PlanResult\n\ndef plan(plan_input: PlanInput) -> PlanResult:\n    return PlanResult()';
    fireEvent.change(editor, { target: { value: newContent } });
    
    // Should show unsaved changes
    await waitFor(() => {
      expect(screen.getByText('●')).toBeInTheDocument();
      expect(saveButton).not.toBeDisabled();
      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
    
    // Save the changes
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('should handle keyboard shortcuts for saving', async () => {
    const mockOnSave = vi.fn();
    render(<CodeEditor file={mockPythonFile} onSave={mockOnSave} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    
    // Make changes to enable save
    fireEvent.change(editor, { target: { value: 'modified content' } });
    
    // Use Ctrl+S shortcut
    fireEvent.keyDown(document, { key: 's', ctrlKey: true });
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('should handle Mac Cmd+S shortcut', async () => {
    const mockOnSave = vi.fn();
    render(<CodeEditor file={mockPythonFile} onSave={mockOnSave} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    
    // Make changes to enable save
    fireEvent.change(editor, { target: { value: 'modified content' } });
    
    // Use Cmd+S shortcut (Mac)
    fireEvent.keyDown(document, { key: 's', metaKey: true });
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('should reset unsaved changes when file changes', async () => {
    const { rerender } = render(<CodeEditor file={mockPythonFile} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    
    // Make changes
    fireEvent.change(editor, { target: { value: 'modified content' } });
    
    await waitFor(() => {
      expect(screen.getByText('●')).toBeInTheDocument();
    });
    
    // Change to different file
    rerender(<CodeEditor file={mockRequirementsFile} />);
    
    await waitFor(() => {
      expect(screen.queryByText('●')).not.toBeInTheDocument();
      expect(screen.getByText('requirements.txt')).toBeInTheDocument();
    });
  });

  it('should show loading state during save operation', async () => {
    const mockOnSave = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<CodeEditor file={mockPythonFile} onSave={mockOnSave} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    fireEvent.change(editor, { target: { value: 'modified content' } });
    
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);
    
    // Should show saving indicator
    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument();
      expect(saveButton).toBeDisabled();
    });
    
    // Should clear after save completes
    await waitFor(() => {
      expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
    }, { timeout: 200 });
  });
});