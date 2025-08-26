import React, { useRef, useState, useCallback, useEffect } from 'react';
import './GraphCanvas.css';

export type ToolType = 'select' | 'task' | 'plan';

export interface CanvasNode {
  id: string;
  type: 'task' | 'plan';
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  selected: boolean;
}

export interface CanvasEdge {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  selected: boolean;
}

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}



export interface GraphCanvasProps {
  graph?: any;
  selectedTool: ToolType;
  onToolChange: (tool: ToolType) => void;
  onNodeCreate?: (node: Omit<CanvasNode, 'id' | 'selected'>) => void;
  onEdgeCreate?: (edge: Omit<CanvasEdge, 'id' | 'selected'>) => void;
  onNodeSelect?: (nodeId: string) => void;
  onNodeDelete?: (nodeId: string) => void;
  onEdgeDelete?: (edgeId: string) => void;
  onNodeMove?: (nodeId: string, x: number, y: number) => void;
  onNodeUpdate?: (nodeId: string, updates: Partial<CanvasNode>) => void;
  showValidation?: boolean;
  onValidationChange?: (result: any) => void;
}

const GraphCanvas: React.FC<GraphCanvasProps> = ({
  graph,
  selectedTool,
  onToolChange,
  onNodeCreate,
  onNodeSelect,
  onNodeMove,
  onNodeUpdate
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, zoom: 1 });
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [edges, setEdges] = useState<CanvasEdge[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState<string | null>(null);
  const [isDrawingNode, setIsDrawingNode] = useState(false);
  const [nodePreview, setNodePreview] = useState<{
    startX: number;
    startY: number;
    currentX: number;
    currentY: number;
    type: 'task' | 'plan';
  } | null>(null);
  
  // Node editing state
  const [editingNode, setEditingNode] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState('');
  


  // Convert screen coordinates to world coordinates
  const screenToWorld = useCallback((screenX: number, screenY: number) => {
    return {
      x: (screenX - viewport.x) / viewport.zoom,
      y: (screenY - viewport.y) / viewport.zoom
    };
  }, [viewport]);

  // Convert world coordinates to screen coordinates
  const worldToScreen = useCallback((worldX: number, worldY: number) => {
    return {
      x: worldX * viewport.zoom + viewport.x,
      y: worldY * viewport.zoom + viewport.y
    };
  }, [viewport]);







  // Draw a node
  const drawNode = useCallback((ctx: CanvasRenderingContext2D, node: CanvasNode) => {
    const screenPos = worldToScreen(node.x, node.y);
    const scaledWidth = node.width * viewport.zoom;
    const scaledHeight = node.height * viewport.zoom;
    
    // Set styles
    ctx.fillStyle = node.selected ? '#e3f2fd' : '#e8f4fd';
    ctx.strokeStyle = node.selected ? '#2196f3' : '#1976d2';
    ctx.lineWidth = node.selected ? 3 : 2;
    
    if (node.type === 'task') {
      // Draw rectangle for task
      ctx.fillRect(screenPos.x, screenPos.y, scaledWidth, scaledHeight);
      ctx.strokeRect(screenPos.x, screenPos.y, scaledWidth, scaledHeight);
    } else {
      // Draw circle for plan
      const centerX = screenPos.x + scaledWidth / 2;
      const centerY = screenPos.y + scaledHeight / 2;
      const radius = Math.min(scaledWidth, scaledHeight) / 2;
      
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    }
    
    // Draw label
    ctx.fillStyle = '#333333';
    ctx.font = `${12 * viewport.zoom}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const centerX = screenPos.x + scaledWidth / 2;
    const centerY = screenPos.y + scaledHeight / 2;
    
    ctx.fillText(node.label, centerX, centerY);
  }, [viewport, worldToScreen]);

  // Draw an edge
  const drawEdge = useCallback((ctx: CanvasRenderingContext2D, edge: CanvasEdge) => {
    const fromNode = nodes.find(n => n.id === edge.fromNodeId);
    const toNode = nodes.find(n => n.id === edge.toNodeId);
    
    if (!fromNode || !toNode) return;
    
    const fromCenterX = fromNode.x + fromNode.width / 2;
    const fromCenterY = fromNode.y + fromNode.height / 2;
    const toCenterX = toNode.x + toNode.width / 2;
    const toCenterY = toNode.y + toNode.height / 2;
    
    const fromScreen = worldToScreen(fromCenterX, fromCenterY);
    const toScreen = worldToScreen(toCenterX, toCenterY);
    
    ctx.strokeStyle = edge.selected ? '#2196f3' : '#666666';
    ctx.lineWidth = edge.selected ? 3 : 2;
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(fromScreen.x, fromScreen.y);
    ctx.lineTo(toScreen.x, toScreen.y);
    ctx.stroke();
  }, [nodes, viewport, worldToScreen]);

  // Draw node preview (rubber band)
  const drawNodePreview = useCallback((ctx: CanvasRenderingContext2D) => {
    if (!nodePreview) return;
    
    const startScreen = worldToScreen(nodePreview.startX, nodePreview.startY);
    const currentScreen = worldToScreen(nodePreview.currentX, nodePreview.currentY);
    
    // Calculate preview dimensions
    const x = Math.min(startScreen.x, currentScreen.x);
    const y = Math.min(startScreen.y, currentScreen.y);
    const width = Math.abs(currentScreen.x - startScreen.x);
    const height = Math.abs(currentScreen.y - startScreen.y);
    
    // Draw preview rectangle
    ctx.strokeStyle = '#2196f3';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(x, y, width, height);
    ctx.setLineDash([]);
  }, [nodePreview, worldToScreen]);

  // Draw grid
  const drawGrid = useCallback((ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
    const gridSize = 20 * viewport.zoom;
    
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    
    // Draw vertical lines
    for (let x = -viewport.x % gridSize; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = -viewport.y % gridSize; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }, [viewport]);

  // Main render function
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid
    drawGrid(ctx, canvas);
    
    // Draw edges
    edges.forEach(edge => {
      drawEdge(ctx, edge);
    });
    
    // Draw nodes
    nodes.forEach(node => {
      drawNode(ctx, node);
    });
    
    // Draw node preview
    if (isDrawingNode && nodePreview) {
      drawNodePreview(ctx);
    }
  }, [drawGrid, drawEdge, drawNode, drawNodePreview, nodes, edges, isDrawingNode, nodePreview]);

  // Request render
  const requestRender = useCallback(() => {
    requestAnimationFrame(render);
  }, [render]);

  // Handle double click for editing
  const handleDoubleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const worldPos = screenToWorld(x, y);
    
    const clickedNode = nodes.find(node => 
      worldPos.x >= node.x && 
      worldPos.x <= node.x + node.width &&
      worldPos.y >= node.y && 
      worldPos.y <= node.y + node.height
    );
    
    if (clickedNode) {
      setEditingNode(clickedNode.id);
      setEditLabel(clickedNode.label);
    }
  }, [nodes, screenToWorld]);

  // Handle mouse down
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (selectedTool === 'select') {
      // Check if clicking on a node
      const worldPos = screenToWorld(x, y);
      const clickedNode = nodes.find(node => 
        worldPos.x >= node.x && 
        worldPos.x <= node.x + node.width &&
        worldPos.y >= node.y && 
        worldPos.y <= node.y + node.height
      );
      
      if (clickedNode) {
        setIsDragging(true);
        setDraggedNode(clickedNode.id);
        setDragStart({ x: worldPos.x - clickedNode.x, y: worldPos.y - clickedNode.y });
        onNodeSelect?.(clickedNode.id);
        return;
      }
    } else if (selectedTool === 'task' || selectedTool === 'plan') {
      // Start drawing a node
      const worldPos = screenToWorld(x, y);
      setIsDrawingNode(true);
      setNodePreview({
        startX: worldPos.x,
        startY: worldPos.y,
        currentX: worldPos.x,
        currentY: worldPos.y,
        type: selectedTool as 'task' | 'plan'
      });
      return;
    }
    
    setIsDragging(true);
    setDragStart({ x, y });
  }, [selectedTool, nodes, screenToWorld, onNodeSelect]);

  // Handle mouse move
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (draggedNode) {
      // Move node
      const worldPos = screenToWorld(x, y);
      const newX = worldPos.x - dragStart.x;
      const newY = worldPos.y - dragStart.y;
      
      setNodes(prev => prev.map(node => 
        node.id === draggedNode 
          ? { ...node, x: newX, y: newY }
          : node
      ));
      
      onNodeMove?.(draggedNode, newX, newY);
      requestRender();
    } else if (isDrawingNode && nodePreview) {
      // Update node preview
      const worldPos = screenToWorld(x, y);
      setNodePreview(prev => prev ? {
        ...prev,
        currentX: worldPos.x,
        currentY: worldPos.y
      } : null);
      requestRender();
    } else if (isDragging) {
      // Pan viewport
      const deltaX = x - dragStart.x;
      const deltaY = y - dragStart.y;
      
      setViewport(prev => ({
        ...prev,
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }));
      
      setDragStart({ x, y });
      requestRender();
    }
  }, [draggedNode, dragStart, isDrawingNode, nodePreview, isDragging, screenToWorld, onNodeMove, requestRender]);

  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    if (isDrawingNode && nodePreview) {
      // Finish node creation
      const startX = Math.min(nodePreview.startX, nodePreview.currentX);
      const startY = Math.min(nodePreview.startY, nodePreview.currentY);
      const width = Math.abs(nodePreview.currentX - nodePreview.startX);
      const height = Math.abs(nodePreview.currentY - nodePreview.startY);
      
      // Only create node if it has reasonable dimensions
      if (width > 20 && height > 20) {
        const newNode: Omit<CanvasNode, 'id' | 'selected'> = {
          type: nodePreview.type,
          x: startX,
          y: startY,
          width: width,
          height: height,
          label: `New ${nodePreview.type}`
        };
        
        onNodeCreate?.(newNode);
      }
      
      setIsDrawingNode(false);
      setNodePreview(null);
    }
    
    setIsDragging(false);
    setDraggedNode(null);
  }, [isDrawingNode, nodePreview, onNodeCreate]);

  // Handle wheel for zooming
  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.1, Math.min(5, viewport.zoom * zoomFactor));
    
    // Zoom towards mouse position
    const worldPos = screenToWorld(x, y);
    const newViewport = {
      x: x - worldPos.x * newZoom,
      y: y - worldPos.y * newZoom,
      zoom: newZoom
    };
    
    setViewport(newViewport);
    requestRender();
  }, [viewport, screenToWorld, requestRender]);

  // Handle label editing
  const handleLabelSubmit = useCallback(() => {
    if (editingNode && editLabel.trim()) {
      onNodeUpdate?.(editingNode, { label: editLabel.trim() });
      setNodes(prev => prev.map(node => 
        node.id === editingNode 
          ? { ...node, label: editLabel.trim() }
          : node
      ));
    }
    setEditingNode(null);
    setEditLabel('');
  }, [editingNode, editLabel, onNodeUpdate]);

  const handleLabelCancel = useCallback(() => {
    setEditingNode(null);
    setEditLabel('');
  }, []);

  // Initialize nodes and edges from graph data
  useEffect(() => {
    if (!graph) return;

    const newNodes: CanvasNode[] = [];
    const newEdges: CanvasEdge[] = [];

    // Convert plans to nodes
    graph.plans.forEach((plan: any, index: number) => {
      const node: CanvasNode = {
        id: plan.name,
        type: 'plan',
        x: 200 + index * 150,
        y: 100 + index * 100,
        width: 100,
        height: 100,
        label: plan.label || plan.name,
        selected: false
      };
      newNodes.push(node);
    });

    // Convert tasks to nodes
    graph.tasks.forEach((task: any, index: number) => {
      const node: CanvasNode = {
        id: task.name,
        type: 'task',
        x: 200 + index * 150,
        y: 300 + index * 100,
        width: 120,
        height: 80,
        label: task.label || task.name,
        selected: false
      };
      newNodes.push(node);
    });

    // Convert relationships to edges
    Object.entries(graph.planToTasks || {}).forEach(([planId, taskIds]: [string, any]) => {
      taskIds.forEach((taskId: string) => {
        newEdges.push({
          id: `${planId}-${taskId}`,
          fromNodeId: planId,
          toNodeId: taskId,
          selected: false
        });
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [graph]);



  // Request render when dependencies change
  useEffect(() => {
    requestRender();
  }, [nodes, edges, viewport, isDrawingNode, nodePreview, requestRender]);

  // Set up canvas and resize handling
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    
    const resizeCanvas = () => {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      requestRender();
    };
    
    resizeCanvas();
    
    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [requestRender]);

  return (
    <div className="graph-canvas" ref={containerRef}>
      <div className="canvas-toolbar">
        <div className="toolbar-group">
          <button 
            className={`tool-button ${selectedTool === 'select' ? 'active' : ''}`}
            onClick={() => onToolChange('select')}
          >
            Select
          </button>
          <button 
            className={`tool-button ${selectedTool === 'task' ? 'active' : ''}`}
            onClick={() => onToolChange('task')}
          >
            Task
          </button>
          <button 
            className={`tool-button ${selectedTool === 'plan' ? 'active' : ''}`}
            onClick={() => onToolChange('plan')}
          >
            Plan
          </button>
        </div>
      </div>
      
      <canvas
        ref={canvasRef}
        className="canvas-content"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onDoubleClick={handleDoubleClick}
      />
      
      {/* Node label editing overlay */}
      {editingNode && (
        <div className="node-edit-overlay">
          <input
            type="text"
            value={editLabel}
            onChange={(e) => setEditLabel(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleLabelSubmit();
              if (e.key === 'Escape') handleLabelCancel();
            }}
            onBlur={handleLabelSubmit}
            autoFocus
            className="node-edit-input"
          />
        </div>
      )}
    </div>
  );
};

export default GraphCanvas;