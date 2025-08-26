import React, { useState } from 'react';
import './CreateGraphDialog.css';

interface CreateGraphDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (graphName: string) => void;
  loading?: boolean;
}

const CreateGraphDialog: React.FC<CreateGraphDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  loading = false,
}) => {
  const [graphName, setGraphName] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedName = graphName.trim();
    if (!trimmedName) {
      setError('Graph name is required');
      return;
    }
    
    if (trimmedName.length < 3) {
      setError('Graph name must be at least 3 characters long');
      return;
    }
    
    if (!/^[a-zA-Z0-9_-\s]+$/.test(trimmedName)) {
      setError('Graph name can only contain letters, numbers, spaces, hyphens, and underscores');
      return;
    }
    
    setError('');
    onConfirm(trimmedName);
  };

  const handleClose = () => {
    if (!loading) {
      setGraphName('');
      setError('');
      onClose();
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="create-graph-dialog">
        <h3>Create New Graph</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="graph-name">Graph Name:</label>
            <input
              id="graph-name"
              type="text"
              value={graphName}
              onChange={(e) => setGraphName(e.target.value)}
              placeholder="Enter graph name..."
              className={`form-input ${error ? 'error' : ''}`}
              disabled={loading}
              autoFocus
            />
            {error && <span className="error-text">{error}</span>}
          </div>
          
          <div className="dialog-actions">
            <button
              type="button"
              onClick={handleClose}
              className="cancel-button"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="create-button"
              disabled={loading || !graphName.trim()}
            >
              {loading ? 'Creating...' : 'Create Graph'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateGraphDialog;