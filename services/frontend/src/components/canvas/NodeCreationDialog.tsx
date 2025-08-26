import React, { useState, useCallback } from 'react';
import NodeNameInput from '../validation/NodeNameInput';
import './NodeCreationDialog.css';

export interface NodeCreationDialogProps {
  isOpen: boolean;
  nodeType: 'plan' | 'task';
  graphId: string;
  existingNodeNames: string[];
  onConfirm: (nodeName: string, label: string) => void;
  onCancel: () => void;
}

const NodeCreationDialog: React.FC<NodeCreationDialogProps> = ({
  isOpen,
  nodeType,
  graphId,
  existingNodeNames,
  onConfirm,
  onCancel
}) => {
  const [nodeName, setNodeName] = useState('');
  const [label, setLabel] = useState('');
  const [isValid, setIsValid] = useState(false);

  const handleValidationChange = useCallback((valid: boolean) => {
    setIsValid(valid);
  }, []);

  const handleConfirm = useCallback(() => {
    if (isValid && nodeName.trim()) {
      onConfirm(nodeName.trim(), label.trim() || nodeName.trim());
      // Reset form
      setNodeName('');
      setLabel('');
      setIsValid(false);
    }
  }, [isValid, nodeName, label, onConfirm]);

  const handleCancel = useCallback(() => {
    onCancel();
    // Reset form
    setNodeName('');
    setLabel('');
    setIsValid(false);
  }, [onCancel]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isValid) {
      handleConfirm();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  }, [isValid, handleConfirm, handleCancel]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="node-creation-dialog-overlay" onClick={handleCancel}>
      <div className="node-creation-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h3>Create New {nodeType === 'plan' ? 'Plan' : 'Task'}</h3>
          <button className="close-button" onClick={handleCancel}>×</button>
        </div>
        
        <div className="dialog-content">
          <div className="form-group">
            <label htmlFor="node-name">
              {nodeType === 'plan' ? 'Plan' : 'Task'} Name *
            </label>
            <NodeNameInput
              value={nodeName}
              onChange={setNodeName}
              onValidationChange={handleValidationChange}
              graphId={graphId}
              existingNodeNames={existingNodeNames}
              placeholder={`Enter ${nodeType} name...`}
              autoFocus={true}
              showValidationFeedback={true}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="node-label">Display Label</label>
            <input
              id="node-label"
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder={`Enter display label (optional)`}
              className="label-input"
              onKeyDown={handleKeyDown}
            />
            <div className="form-help">
              If empty, the name will be used as the label
            </div>
          </div>
        </div>
        
        <div className="dialog-actions">
          <button 
            className="cancel-button" 
            onClick={handleCancel}
          >
            Cancel
          </button>
          <button 
            className="confirm-button" 
            onClick={handleConfirm}
            disabled={!isValid || !nodeName.trim()}
          >
            Create {nodeType === 'plan' ? 'Plan' : 'Task'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodeCreationDialog;