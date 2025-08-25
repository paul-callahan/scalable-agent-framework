import React, { useCallback, useState } from 'react';
import ThreePaneLayout from '../components/layout/ThreePaneLayout';
import AppHeader from '../components/layout/AppHeader';
import FileExplorer from '../components/file-explorer/FileExplorer';
import GraphCanvas, { type ToolType, type CanvasNode, type CanvasEdge } from '../components/canvas/GraphCanvas';
import CodeEditor from '../components/editor/CodeEditor';
import { useAppContext } from '../hooks/useAppContext';
import { graphApi } from '../api/client';

const GraphEditor: React.FC = () => {
  const { state, dispatch } = useAppContext();
  const { selectedFile, currentGraph } = state;
  const [selectedTool, setSelectedTool] = useState<ToolType>('select');

  // Determine language based on file extension
  const getLanguage = (fileName: string): 'python' | 'plaintext' => {
    return fileName.endsWith('.py') ? 'python' : 'plaintext';
  };

  // Handle file content changes
  const handleFileChange = useCallback((content: string) => {
    if (!selectedFile) return;
    
    // Update the file content in the current graph and selected file
    dispatch({ 
      type: 'UPDATE_FILE_CONTENT', 
      payload: { fileName: selectedFile.name, content } 
    });
  }, [selectedFile, dispatch]);

  // Handle complete graph save (replaces individual file saves)
  const handleGraphSave = useCallback(async () => {
    if (!currentGraph || !currentGraph.id) return;

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      // Save the entire graph with all files
      const updatedGraph = await graphApi.updateGraph(currentGraph.id, currentGraph);
      
      // Update the current graph with the response from server
      dispatch({ type: 'SET_CURRENT_GRAPH', payload: updatedGraph });
      
      console.log('Graph saved successfully');
    } catch (error) {
      console.error('Failed to save graph:', error);
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Failed to save graph. Please try again.' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [currentGraph, dispatch]);

  // Handle tool changes
  const handleToolChange = useCallback((tool: ToolType) => {
    setSelectedTool(tool);
  }, []);

  // Handle node creation (placeholder - will be implemented in later tasks)
  const handleNodeCreate = useCallback((node: Omit<CanvasNode, 'id' | 'selected'>) => {
    console.log('Node creation requested:', node);
    // TODO: Implement node creation in backend integration
  }, []);

  // Handle edge creation (placeholder - will be implemented in later tasks)
  const handleEdgeCreate = useCallback((edge: Omit<CanvasEdge, 'id' | 'selected'>) => {
    console.log('Edge creation requested:', edge);
    // TODO: Implement edge creation in backend integration
  }, []);

  // Handle node selection
  const handleNodeSelect = useCallback((nodeId: string) => {
    console.log('Node selected:', nodeId);
    // TODO: Expand corresponding folder in file explorer
  }, []);

  // Handle node deletion (placeholder - will be implemented in later tasks)
  const handleNodeDelete = useCallback((nodeId: string) => {
    console.log('Node deletion requested:', nodeId);
    // TODO: Implement node deletion in backend integration
  }, []);

  // Handle edge deletion (placeholder - will be implemented in later tasks)
  const handleEdgeDelete = useCallback((edgeId: string) => {
    console.log('Edge deletion requested:', edgeId);
    // TODO: Implement edge deletion in backend integration
  }, []);

  // Handle node movement (placeholder - will be implemented in later tasks)
  const handleNodeMove = useCallback((nodeId: string, x: number, y: number) => {
    console.log('Node moved:', nodeId, x, y);
    // TODO: Implement node position updates in backend integration
  }, []);

  return (
    <ThreePaneLayout
      header={
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <AppHeader />
          {currentGraph && (
            <button 
              onClick={handleGraphSave}
              disabled={state.isLoading}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: state.isLoading ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              {state.isLoading ? 'Saving...' : 'Save Graph'}
            </button>
          )}
        </div>
      }
      leftPane={<FileExplorer />}
      centerTopPane={
        <GraphCanvas
          graph={currentGraph || undefined}
          selectedTool={selectedTool}
          onToolChange={handleToolChange}
          onNodeCreate={handleNodeCreate}
          onEdgeCreate={handleEdgeCreate}
          onNodeSelect={handleNodeSelect}
          onNodeDelete={handleNodeDelete}
          onEdgeDelete={handleEdgeDelete}
          onNodeMove={handleNodeMove}
        />
      }
      centerBottomPane={
        <CodeEditor
          file={selectedFile || undefined}
          language={selectedFile ? getLanguage(selectedFile.name) : 'python'}
          onChange={handleFileChange}
          onSave={handleGraphSave}
        />
      }
    />
  );
};

export default GraphEditor;