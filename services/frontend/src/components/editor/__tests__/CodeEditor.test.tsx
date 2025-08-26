import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import CodeEditor from '../CodeEditor';
import type { ExecutorFile } from '../../../types';

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

describe('CodeEditor', () => {
  const mockFile: ExecutorFile = {
    name: 'test.py',
    contents: 'print("Hello, World!")',
    creationDate: '2024-01-01T00:00:00Z',
    version: '1.0',
    updateDate: '2024-01-01T00:00:00Z',
  };

  it('should render placeholder when no file is selected', () => {
    render(<CodeEditor />);
    
    expect(screen.getByText('No file selected')).toBeInTheDocument();
    expect(screen.getByText('Select a file from the file explorer to start editing')).toBeInTheDocument();
  });

  it('should render file content when file is provided', () => {
    render(<CodeEditor file={mockFile} />);
    
    expect(screen.getByText('test.py')).toBeInTheDocument();
    expect(screen.getByDisplayValue('print("Hello, World!")')).toBeInTheDocument();
  });

  it('should show unsaved changes indicator when content is modified', async () => {
    const mockOnChange = vi.fn();
    render(<CodeEditor file={mockFile} onChange={mockOnChange} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    fireEvent.change(editor, { target: { value: 'print("Modified!")' } });
    
    await waitFor(() => {
      expect(screen.getByText('●')).toBeInTheDocument();
      expect(mockOnChange).toHaveBeenCalledWith('print("Modified!")');
    });
  });

  it('should enable save button when there are unsaved changes', async () => {
    render(<CodeEditor file={mockFile} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    const saveButton = screen.getByText('Save');
    
    // Initially disabled
    expect(saveButton).toBeDisabled();
    
    // Modify content
    fireEvent.change(editor, { target: { value: 'print("Modified!")' } });
    
    await waitFor(() => {
      expect(saveButton).not.toBeDisabled();
    });
  });

  it('should call onSave when save button is clicked', async () => {
    const mockOnSave = vi.fn();
    render(<CodeEditor file={mockFile} onSave={mockOnSave} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    fireEvent.change(editor, { target: { value: 'print("Modified!")' } });
    
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('should handle keyboard shortcut Ctrl+S', async () => {
    const mockOnSave = vi.fn();
    render(<CodeEditor file={mockFile} onSave={mockOnSave} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    fireEvent.change(editor, { target: { value: 'print("Modified!")' } });
    
    // Simulate Ctrl+S
    fireEvent.keyDown(document, { key: 's', ctrlKey: true });
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('should show unsaved changes warning', async () => {
    render(<CodeEditor file={mockFile} />);
    
    const editor = screen.getByTestId('codemirror-editor');
    fireEvent.change(editor, { target: { value: 'print("Modified!")' } });
    
    await waitFor(() => {
      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
  });

  it('should determine language correctly', () => {
    const pythonFile: ExecutorFile = {
      ...mockFile,
      name: 'script.py',
    };
    
    const txtFile: ExecutorFile = {
      ...mockFile,
      name: 'requirements.txt',
    };
    
    render(<CodeEditor file={pythonFile} language="python" />);
    expect(screen.getByText('script.py')).toBeInTheDocument();
    
    render(<CodeEditor file={txtFile} language="plaintext" />);
    expect(screen.getByText('requirements.txt')).toBeInTheDocument();
  });
});