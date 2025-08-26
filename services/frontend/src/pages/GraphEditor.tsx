import React, { useCallback, useState, useEffect } from 'react';
import ThreePaneLayout from '../components/layout/ThreePaneLayout';
import AppHeader from '../components/layout/AppHeader';
import FileExplorer from '../components/file-explorer/FileExplorer';
import GraphCanvas, { type ToolType, type CanvasNode, type CanvasEdge } from '../components/canvas/GraphCanvas';
import CodeEditor from '../components/editor/CodeEditor';
import { useAppContext } from '../hooks/useAppContext';
import { graphApi } from '../api/client';
import type { AgentGraphDto } from '../types';

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

      // Validate the graph before saving
      const validatedGraph: AgentGraphDto = {
        ...currentGraph,
        plans: [...(currentGraph.plans || [])],
        tasks: [...(currentGraph.tasks || [])],
        planToTasks: { ...currentGraph.planToTasks },
        taskToPlan: { ...currentGraph.taskToPlan }
      };
      console.log('Validated graph:', validatedGraph);
      
      // Use POST for new graphs, PUT for existing graphs
      let updatedGraph: AgentGraphDto;
      if (currentGraph.id.startsWith('new-')) {
        // Create new graph
        const createRequest = {
          name: validatedGraph.name,
          tenantId: validatedGraph.tenantId
        };
        console.log('Creating new graph with:', createRequest);
        updatedGraph = await graphApi.createGraph(createRequest);
      } else {
        // Update existing graph
        console.log('Updating existing graph');
        updatedGraph = await graphApi.updateGraph(validatedGraph.id, validatedGraph);
      }
      
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
  }, [dispatch]);

  // Handle tool changes
  const handleToolChange = useCallback((tool: ToolType) => {
    setSelectedTool(tool);
  }, []);

  // Handle node creation (placeholder - will be implemented in later tasks)
  const handleNodeCreate = useCallback((node: Omit<CanvasNode, 'id' | 'selected'>) => {
    console.log('Node creation requested:', node);
    console.log('Current graph before update:', currentGraph);
    
    // Add the node to the current graph if it exists
    if (currentGraph) {
      // Create a completely new graph object to ensure React detects the change
      const updatedGraph = {
        ...currentGraph,
        plans: [...(currentGraph.plans || [])],
        tasks: [...(currentGraph.tasks || [])],
        planToTasks: { ...currentGraph.planToTasks },
        taskToPlan: { ...currentGraph.taskToPlan }
      };
      
      if (node.type === 'plan') {
        // Add new plan to the graph
        const newPlan = {
          name: node.label,
          label: node.label,
          upstreamTaskIds: [],
          files: []
        };
        updatedGraph.plans.push(newPlan);
        console.log('Added new plan:', newPlan);
      } else if (node.type === 'task') {
        // Add new task to the graph
        const newTask = {
          name: node.label,
          label: node.label,
          upstreamPlanId: '',
          files: []
        };
        updatedGraph.tasks.push(newTask);
        console.log('Added new task:', newTask);
      }
      
      console.log('Updated graph:', updatedGraph);
      
      // Update the current graph in state
      dispatch({ type: 'SET_CURRENT_GRAPH', payload: updatedGraph });
    }
  }, [currentGraph, dispatch]);

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

  // Handle node updates (label changes, etc.)
  const handleNodeUpdate = useCallback((nodeId: string, updates: Partial<CanvasNode>) => {
    if (updates.label && currentGraph) {
      // Create a completely new graph object to ensure React detects the change
      const updatedGraph = {
        ...currentGraph,
        plans: [...(currentGraph.plans || [])],
        tasks: [...(currentGraph.tasks || [])],
        planToTasks: { ...currentGraph.planToTasks },
        taskToPlan: { ...currentGraph.taskToPlan }
      };
      
      // Update plan label
      updatedGraph.plans = updatedGraph.plans.map((plan: any) => 
        plan.name === nodeId ? { ...plan, label: updates.label! } : plan
      );
      
      // Update task label
      updatedGraph.tasks = updatedGraph.tasks.map((task: any) => 
        task.name === nodeId ? { ...task, label: updates.label! } : task
      );
      
      // Update the current graph in state
      dispatch({ type: 'SET_CURRENT_GRAPH', payload: updatedGraph });
    }
  }, [currentGraph, dispatch]);

  // Initialize currentGraph when component mounts (for new graphs)
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const graphName = searchParams.get('name');
    
    if (graphName && !currentGraph) {
      // Create a new graph structure for the new graph
      const newGraph = {
        id: `new-${Date.now()}`,
        name: graphName,
        tenantId: 'evil-corp', // Default tenant
        status: 'NEW' as const,
        plans: [],
        tasks: [],
        planToTasks: {},
        taskToPlan: {},
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      console.log('Initializing new graph:', newGraph);
      dispatch({ type: 'SET_CURRENT_GRAPH', payload: newGraph });
    }
  }, [dispatch]);

  // Debug: Log when currentGraph changes
  useEffect(() => {
    console.log('GraphEditor: currentGraph changed:', currentGraph);
  }, [currentGraph]);

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
          onNodeUpdate={handleNodeUpdate}
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