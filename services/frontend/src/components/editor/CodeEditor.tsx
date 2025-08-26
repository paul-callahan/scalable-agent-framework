import React, { useState, useEffect, useCallback } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { EditorView } from '@codemirror/view';
import type { ExecutorFile } from '../../types';
import './CodeEditor.css';

interface CodeEditorProps {
  file?: ExecutorFile;
  language?: 'python' | 'plaintext';
  onChange?: (content: string) => void;
  onSave?: () => void;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ 
  file, 
  language = 'python', 
  onChange, 
  onSave 
}) => {
  const [content, setContent] = useState<string>('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Load file content when file changes
  useEffect(() => {
    if (file) {
      setContent(file.contents);
      setHasUnsavedChanges(false);
    } else {
      setContent('');
      setHasUnsavedChanges(false);
    }
  }, [file]);

  // Handle content changes
  const handleContentChange = useCallback((value: string) => {
    setContent(value);
    setHasUnsavedChanges(value !== (file?.contents || ''));
    onChange?.(value);
  }, [file?.contents, onChange]);

  // Handle save operation
  const handleSave = useCallback(async () => {
    if (!hasUnsavedChanges || !onSave) return;
    
    setIsLoading(true);
    try {
      await onSave();
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Failed to save file:', error);
    } finally {
      setIsLoading(false);
    }
  }, [hasUnsavedChanges, onSave]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleSave();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  // CodeMirror extensions
  const extensions = [
    EditorView.theme({
      '&': {
        fontSize: '14px',
        fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", monospace',
      },
      '.cm-content': {
        padding: '16px',
        minHeight: '100%',
      },
      '.cm-focused': {
        outline: 'none',
      },
      '.cm-editor': {
        height: '100%',
      },
      '.cm-scroller': {
        height: '100%',
      },
    }),
    EditorView.lineWrapping,
  ];

  // Add Python language support if needed
  if (language === 'python') {
    extensions.push(python());
  }

  // Show unsaved changes warning
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  if (!file) {
    return (
      <div className="code-editor">
        <div className="editor-placeholder">
          <div className="placeholder-content">
            <h3>No file selected</h3>
            <p>Select a file from the file explorer to start editing</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="code-editor">
      <div className="editor-header">
        <div className="editor-file-info">
          <span className="file-name">{file.name}</span>
          {hasUnsavedChanges && <span className="unsaved-indicator">●</span>}
          {isLoading && <span className="saving-indicator">Saving...</span>}
        </div>
        <div className="editor-actions">
          <button
            className="save-button"
            onClick={handleSave}
            disabled={!hasUnsavedChanges || isLoading}
            title="Save (Ctrl+S)"
          >
            Save
          </button>
        </div>
      </div>
      <div className="editor-content">
        <CodeMirror
          value={content}
          onChange={handleContentChange}
          extensions={extensions}
          basicSetup={{
            lineNumbers: true,
            foldGutter: true,
            dropCursor: false,
            allowMultipleSelections: false,
            indentOnInput: true,
            bracketMatching: true,
            closeBrackets: true,
            autocompletion: true,
            highlightSelectionMatches: false,
            searchKeymap: true,
          }}
        />
      </div>
      {hasUnsavedChanges && (
        <div className="unsaved-changes-warning">
          <span>You have unsaved changes</span>
        </div>
      )}
    </div>
  );
};

export default CodeEditor;