import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from '../components/layout/AppHeader';
import GraphList from '../components/graph-list/GraphList';
import CreateGraphDialog from '../components/graph-list/CreateGraphDialog';
import { useGraphs } from '../hooks/useGraphs';
import { useAppContext } from '../hooks/useAppContext';
import './GraphManagement.css';

const GraphManagement: React.FC = () => {
  const navigate = useNavigate();
  const { state } = useAppContext();
  const { graphs, loadGraph, deleteGraph, submitForExecution, createGraph } = useGraphs();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const handleCreateNew = () => {
    setShowCreateDialog(true);
  };

  const handleCreateConfirm = async (graphName: string) => {
    try {
      await createGraph({ name: graphName, tenantId: state.tenantId });
      setShowCreateDialog(false);
      navigate('/editor');
    } catch (error) {
      // Error is already handled by the hook
      console.error('Failed to create graph:', error);
    }
  };

  const handleCreateCancel = () => {
    setShowCreateDialog(false);
  };

  const handleLoadGraph = async (graphId: string) => {
    try {
      await loadGraph(graphId);
      navigate('/editor');
    } catch (error) {
      // Error is already handled by the hook
      console.error('Failed to load graph:', error);
    }
  };

  const handleDeleteGraph = async (graphId: string) => {
    try {
      await deleteGraph(graphId);
    } catch (error) {
      // Error is already handled by the hook
      console.error('Failed to delete graph:', error);
    }
  };

  const handleSubmitForExecution = async (graphId: string) => {
    try {
      await submitForExecution(graphId);
    } catch (error) {
      // Error is already handled by the hook
      console.error('Failed to submit for execution:', error);
    }
  };

  return (
    <div className="graph-management">
      <AppHeader />
      
      <main className="management-content">
        <GraphList
          graphs={graphs}
          loading={state.isLoading}
          error={state.error}
          onLoadGraph={handleLoadGraph}
          onDeleteGraph={handleDeleteGraph}
          onSubmitForExecution={handleSubmitForExecution}
          onCreateNew={handleCreateNew}
        />
        
        <CreateGraphDialog
          isOpen={showCreateDialog}
          onClose={handleCreateCancel}
          onConfirm={handleCreateConfirm}
          loading={state.isLoading}
        />
      </main>
    </div>
  );
};

export default GraphManagement;