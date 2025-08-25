import React, { useRef, useEffect, useState, useCallback } from 'react';
import ValidationOverlay from './ValidationOverlay';
import ValidationStatusBar from '../validation/ValidationStatusBar';
import { useValidation } from '../../hooks/useValidation';
import type { AgentGraphDto, ValidationResult } from '../../types';
import './GraphCanvas.css';

export type ToolType = 'select' | 'task' | 'plan' | 'edge';

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
  graph?: AgentGraphDto;
  selectedTool: ToolType;
  onToolChange: (tool: ToolType) => void;
  onNodeCreate?: (node: Omit<CanvasNode, 'id' | 'selected'>) => void;
  onEdgeCreate?: (edge: Omit<CanvasEdge, 'id' | 'selected'>) => void;
  onNodeSelect?: (nodeId: string) => void;
  onNodeDelete?: (nodeId: string) => void;
  onEdgeDelete?: (edgeId: string) => void;
  onNodeMove?: (nodeId: string, x: number, y: number) => void;
  showValidation?: boolean;
  onValidationChange?: (result: ValidationResult) => void;
}

const GRID_SIZE = 20;
const NODE_TASK_SIZE = { width: 120, height: 80 };
const NODE_PLAN_SIZE = { width: 100, height: 100 };

// True tiling system constants
const TILE_SIZE = 512; // Size of each tile in world coordinates
const RENDER_THROTTLE_MS = 16; // ~60fps throttling

// Tile system interfaces
interface Tile {
  x: number; // Tile grid x coordinate
  y: number; // Tile grid y coordinate
  worldX: number; // World x coordinate of tile top-left
  worldY: number; // World y coordinate of tile top-left
  nodes: Set<string>; // Node IDs in this tile
  edges: Set<string>; // Edge IDs that pass through this tile
  isDirty: boolean; // Whether tile needs re-rendering
  canvas?: HTMLCanvasElement; // Cached tile canvas
}

interface TileSystem {
  tiles: Map<string, Tile>; // Key: "x,y"
  nodeToTiles: Map<string, Set<string>>; // Node ID to tile keys
  edgeToTiles: Map<string, Set<string>>; // Edge ID to tile keys
}

const GraphCanvas: React.FC<GraphCanvasProps> = ({
  graph,
  selectedTool,
  onToolChange,
  onNodeCreate,
  onEdgeCreate,
  onNodeSelect,
  onNodeDelete,
  onEdgeDelete,
  onNodeMove,
  showValidation = true,
  onValidationChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, zoom: 1 });
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [edges, setEdges] = useState<CanvasEdge[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState<string | null>(null);
  const [isDrawingEdge, setIsDrawingEdge] = useState(false);
  const [edgeStart, setEdgeStart] = useState<{ nodeId: string; x: number; y: number } | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  
  // Validation state
  const { validateGraph, validateGraphSync, validationState } = useValidation();
  const [showValidationOverlay, setShowValidationOverlay] = useState(false);
  const [validationOverlayPosition] = useState({ x: 20, y: 20 });

  // Tiling system state
  const [tileSystem, setTileSystem] = useState<TileSystem>({
    tiles: new Map(),
    nodeToTiles: new Map(),
    edgeToTiles: new Map()
  });
  const [lastRenderTime, setLastRenderTime] = useState(0);
  const [renderRequested, setRenderRequested] = useState(false);
  const validationTimeoutRef = useRef<number | null>(null);
  const renderTimeoutRef = useRef<number | null>(null);

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

  // Tiling system functions
  const getTileKey = useCallback((tileX: number, tileY: number): string => {
    return `${tileX},${tileY}`;
  }, []);

  const worldToTile = useCallback((worldX: number, worldY: number): { tileX: number; tileY: number } => {
    return {
      tileX: Math.floor(worldX / TILE_SIZE),
      tileY: Math.floor(worldY / TILE_SIZE)
    };
  }, []);

  const getTilesForBounds = useCallback((left: number, top: number, right: number, bottom: number): string[] => {
    const topLeft = worldToTile(left, top);
    const bottomRight = worldToTile(right, bottom);
    
    const tileKeys: string[] = [];
    for (let tileX = topLeft.tileX; tileX <= bottomRight.tileX; tileX++) {
      for (let tileY = topLeft.tileY; tileY <= bottomRight.tileY; tileY++) {
        tileKeys.push(getTileKey(tileX, tileY));
      }
    }
    return tileKeys;
  }, [worldToTile, getTileKey]);

  const getOrCreateTile = useCallback((tileX: number, tileY: number): Tile => {
    const key = getTileKey(tileX, tileY);
    let tile = tileSystem.tiles.get(key);
    
    if (!tile) {
      tile = {
        x: tileX,
        y: tileY,
        worldX: tileX * TILE_SIZE,
        worldY: tileY * TILE_SIZE,
        nodes: new Set(),
        edges: new Set(),
        isDirty: true
      };
      
      setTileSystem(prev => ({
        ...prev,
        tiles: new Map(prev.tiles).set(key, tile!)
      }));
    }
    
    return tile;
  }, [tileSystem.tiles, getTileKey]);

  const addNodeToTiles = useCallback((node: CanvasNode) => {
    const nodeBounds = {
      left: node.x,
      top: node.y,
      right: node.x + node.width,
      bottom: node.y + node.height
    };
    
    const tileKeys = getTilesForBounds(nodeBounds.left, nodeBounds.top, nodeBounds.right, nodeBounds.bottom);
    
    setTileSystem(prev => {
      const newTiles = new Map(prev.tiles);
      const newNodeToTiles = new Map(prev.nodeToTiles);
      
      // Remove node from old tiles
      const oldTileKeys = newNodeToTiles.get(node.id) || new Set();
      oldTileKeys.forEach(tileKey => {
        const tile = newTiles.get(tileKey);
        if (tile) {
          tile.nodes.delete(node.id);
          tile.isDirty = true;
        }
      });
      
      // Add node to new tiles
      const newTileKeysSet = new Set(tileKeys);
      tileKeys.forEach(tileKey => {
        const [tileX, tileY] = tileKey.split(',').map(Number);
        const tile = getOrCreateTile(tileX, tileY);
        tile.nodes.add(node.id);
        tile.isDirty = true;
        newTiles.set(tileKey, tile);
      });
      
      newNodeToTiles.set(node.id, newTileKeysSet);
      
      return {
        ...prev,
        tiles: newTiles,
        nodeToTiles: newNodeToTiles
      };
    });
  }, [getTilesForBounds, getOrCreateTile]);

  // Calculate edge connection point on node boundary
  const getNodeConnectionPoint = useCallback((fromNode: CanvasNode, toNode: CanvasNode) => {
    const fromCenterX = fromNode.x + fromNode.width / 2;
    const fromCenterY = fromNode.y + fromNode.height / 2;
    const toCenterX = toNode.x + toNode.width / 2;
    const toCenterY = toNode.y + toNode.height / 2;
    
    const dx = toCenterX - fromCenterX;
    const dy = toCenterY - fromCenterY;
    
    // Calculate connection points on node boundaries
    let fromX = fromCenterX;
    let fromY = fromCenterY;
    let toX = toCenterX;
    let toY = toCenterY;
    
    // For from node
    if (fromNode.type === 'plan') {
      // Circle - calculate intersection with circle
      const radius = Math.min(fromNode.width, fromNode.height) / 2;
      const angle = Math.atan2(dy, dx);
      fromX = fromCenterX + radius * Math.cos(angle);
      fromY = fromCenterY + radius * Math.sin(angle);
    } else {
      // Rectangle - calculate intersection with rectangle edges
      const halfWidth = fromNode.width / 2;
      const halfHeight = fromNode.height / 2;
      
      if (Math.abs(dx) / halfWidth > Math.abs(dy) / halfHeight) {
        // Intersect with left or right edge
        fromX = fromCenterX + (dx > 0 ? halfWidth : -halfWidth);
        fromY = fromCenterY + (dy * halfWidth) / Math.abs(dx);
      } else {
        // Intersect with top or bottom edge
        fromX = fromCenterX + (dx * halfHeight) / Math.abs(dy);
        fromY = fromCenterY + (dy > 0 ? halfHeight : -halfHeight);
      }
    }
    
    // For to node
    if (toNode.type === 'plan') {
      // Circle - calculate intersection with circle
      const radius = Math.min(toNode.width, toNode.height) / 2;
      const angle = Math.atan2(-dy, -dx);
      toX = toCenterX + radius * Math.cos(angle);
      toY = toCenterY + radius * Math.sin(angle);
    } else {
      // Rectangle - calculate intersection with rectangle edges
      const halfWidth = toNode.width / 2;
      const halfHeight = toNode.height / 2;
      
      if (Math.abs(dx) / halfWidth > Math.abs(dy) / halfHeight) {
        // Intersect with left or right edge
        toX = toCenterX + (dx > 0 ? -halfWidth : halfWidth);
        toY = toCenterY + (-dy * halfWidth) / Math.abs(dx);
      } else {
        // Intersect with top or bottom edge
        toX = toCenterX + (-dx * halfHeight) / Math.abs(dy);
        toY = toCenterY + (dy > 0 ? -halfHeight : halfHeight);
      }
    }
    
    return { fromX, fromY, toX, toY };
  }, []);

  const addEdgeToTiles = useCallback((edge: CanvasEdge) => {
    const fromNode = nodes.find(n => n.id === edge.fromNodeId);
    const toNode = nodes.find(n => n.id === edge.toNodeId);
    
    if (!fromNode || !toNode) return;
    
    const { fromX, fromY, toX, toY } = getNodeConnectionPoint(fromNode, toNode);
    
    // Get bounding box of edge
    const edgeBounds = {
      left: Math.min(fromX, toX),
      top: Math.min(fromY, toY),
      right: Math.max(fromX, toX),
      bottom: Math.max(fromY, toY)
    };
    
    const tileKeys = getTilesForBounds(edgeBounds.left, edgeBounds.top, edgeBounds.right, edgeBounds.bottom);
    
    setTileSystem(prev => {
      const newTiles = new Map(prev.tiles);
      const newEdgeToTiles = new Map(prev.edgeToTiles);
      
      // Remove edge from old tiles
      const oldTileKeys = newEdgeToTiles.get(edge.id) || new Set();
      oldTileKeys.forEach(tileKey => {
        const tile = newTiles.get(tileKey);
        if (tile) {
          tile.edges.delete(edge.id);
          tile.isDirty = true;
        }
      });
      
      // Add edge to new tiles
      const newTileKeysSet = new Set(tileKeys);
      tileKeys.forEach(tileKey => {
        const [tileX, tileY] = tileKey.split(',').map(Number);
        const tile = getOrCreateTile(tileX, tileY);
        tile.edges.add(edge.id);
        tile.isDirty = true;
        newTiles.set(tileKey, tile);
      });
      
      newEdgeToTiles.set(edge.id, newTileKeysSet);
      
      return {
        ...prev,
        tiles: newTiles,
        edgeToTiles: newEdgeToTiles
      };
    });
  }, [nodes, getTilesForBounds, getOrCreateTile, getNodeConnectionPoint]);

  const removeNodeFromTiles = useCallback((nodeId: string) => {
    setTileSystem(prev => {
      const newTiles = new Map(prev.tiles);
      const newNodeToTiles = new Map(prev.nodeToTiles);
      
      const tileKeys = newNodeToTiles.get(nodeId) || new Set();
      tileKeys.forEach(tileKey => {
        const tile = newTiles.get(tileKey);
        if (tile) {
          tile.nodes.delete(nodeId);
          tile.isDirty = true;
        }
      });
      
      newNodeToTiles.delete(nodeId);
      
      return {
        ...prev,
        tiles: newTiles,
        nodeToTiles: newNodeToTiles
      };
    });
  }, []);

  const removeEdgeFromTiles = useCallback((edgeId: string) => {
    setTileSystem(prev => {
      const newTiles = new Map(prev.tiles);
      const newEdgeToTiles = new Map(prev.edgeToTiles);
      
      const tileKeys = newEdgeToTiles.get(edgeId) || new Set();
      tileKeys.forEach(tileKey => {
        const tile = newTiles.get(tileKey);
        if (tile) {
          tile.edges.delete(edgeId);
          tile.isDirty = true;
        }
      });
      
      newEdgeToTiles.delete(edgeId);
      
      return {
        ...prev,
        tiles: newTiles,
        edgeToTiles: newEdgeToTiles
      };
    });
  }, []);

  const getVisibleTiles = useCallback((): Tile[] => {
    const canvas = canvasRef.current;
    if (!canvas) return [];
    
    const viewportBounds = {
      left: -viewport.x / viewport.zoom,
      top: -viewport.y / viewport.zoom,
      right: (canvas.width - viewport.x) / viewport.zoom,
      bottom: (canvas.height - viewport.y) / viewport.zoom
    };
    
    const tileKeys = getTilesForBounds(viewportBounds.left, viewportBounds.top, viewportBounds.right, viewportBounds.bottom);
    
    return tileKeys.map(key => tileSystem.tiles.get(key)).filter((tile): tile is Tile => tile !== undefined);
  }, [viewport, tileSystem.tiles, getTilesForBounds]);

  // Initialize nodes and edges from graph data
  useEffect(() => {
    if (!graph) return;

    const newNodes: CanvasNode[] = [];
    const newEdges: CanvasEdge[] = [];

    // Convert plans to nodes
    graph.plans.forEach((plan, index) => {
      newNodes.push({
        id: plan.name,
        type: 'plan',
        x: 200 + (index % 3) * 200,
        y: 100 + Math.floor(index / 3) * 150,
        width: NODE_PLAN_SIZE.width,
        height: NODE_PLAN_SIZE.height,
        label: plan.label || plan.name,
        selected: false
      });
    });

    // Convert tasks to nodes
    graph.tasks.forEach((task, index) => {
      newNodes.push({
        id: task.name,
        type: 'task',
        x: 200 + (index % 3) * 200,
        y: 300 + Math.floor(index / 3) * 150,
        width: NODE_TASK_SIZE.width,
        height: NODE_TASK_SIZE.height,
        label: task.label || task.name,
        selected: false
      });
    });

    // Convert relationships to edges
    Object.entries(graph.planToTasks).forEach(([planId, taskIds]) => {
      taskIds.forEach(taskId => {
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

  // Update tiling system when nodes change
  useEffect(() => {
    nodes.forEach(node => {
      addNodeToTiles(node);
    });
  }, [nodes, addNodeToTiles]);

  // Update tiling system when edges change
  useEffect(() => {
    edges.forEach(edge => {
      addEdgeToTiles(edge);
    });
  }, [edges, addEdgeToTiles]);

  // Optimized validation with improved debouncing
  useEffect(() => {
    if (!graph || !showValidation) return;

    // Clear existing timeout
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }

    const performValidation = () => {
      try {
        // Use client-side validation for immediate feedback
        const result = validateGraphSync(graph);
        onValidationChange?.(result);
        
        // Show validation overlay if there are errors or warnings
        if (result.errors.length > 0 || result.warnings.length > 0) {
          setShowValidationOverlay(true);
        } else {
          setShowValidationOverlay(false);
        }
      } catch (error) {
        console.error('Validation failed:', error);
      }
    };

    // Use shorter debounce for client-side validation since it's fast
    validationTimeoutRef.current = setTimeout(performValidation, 100);
    
    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, [graph, showValidation, validateGraphSync, onValidationChange]);

  // Grid drawing optimized for tiling system
  const drawGrid = useCallback((ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
    const { width, height } = canvas;
    
    // Skip grid drawing if zoomed out too far
    if (viewport.zoom < 0.3) return;
    
    ctx.strokeStyle = viewport.zoom < 0.5 ? '#f0f0f0' : '#e0e0e0';
    ctx.lineWidth = 1;
    
    // Calculate visible area in world coordinates
    const viewportBounds = {
      left: -viewport.x / viewport.zoom,
      top: -viewport.y / viewport.zoom,
      right: (width - viewport.x) / viewport.zoom,
      bottom: (height - viewport.y) / viewport.zoom
    };
    
    const gridSpacing = viewport.zoom < 0.5 ? GRID_SIZE * 2 : GRID_SIZE;
    const startX = Math.floor(viewportBounds.left / gridSpacing) * gridSpacing;
    const endX = Math.ceil(viewportBounds.right / gridSpacing) * gridSpacing;
    const startY = Math.floor(viewportBounds.top / gridSpacing) * gridSpacing;
    const endY = Math.ceil(viewportBounds.bottom / gridSpacing) * gridSpacing;
    
    // Limit grid lines for performance
    const maxLines = 200;
    const xStep = Math.max(gridSpacing, (endX - startX) / maxLines);
    const yStep = Math.max(gridSpacing, (endY - startY) / maxLines);
    
    ctx.beginPath();
    
    // Draw vertical lines
    for (let x = startX; x <= endX; x += xStep) {
      const screenX = x * viewport.zoom + viewport.x;
      if (screenX >= -1 && screenX <= width + 1) {
        ctx.moveTo(screenX, 0);
        ctx.lineTo(screenX, height);
      }
    }
    
    // Draw horizontal lines
    for (let y = startY; y <= endY; y += yStep) {
      const screenY = y * viewport.zoom + viewport.y;
      if (screenY >= -1 && screenY <= height + 1) {
        ctx.moveTo(0, screenY);
        ctx.lineTo(width, screenY);
      }
    }
    
    ctx.stroke();
  }, [viewport]);

  // Draw a node
  const drawNode = useCallback((ctx: CanvasRenderingContext2D, node: CanvasNode) => {
    const screenPos = worldToScreen(node.x, node.y);
    const scaledWidth = node.width * viewport.zoom;
    const scaledHeight = node.height * viewport.zoom;
    
    // Set styles
    ctx.fillStyle = node.selected ? '#e3f2fd' : '#ffffff';
    ctx.strokeStyle = node.selected ? '#2196f3' : '#666666';
    ctx.lineWidth = node.selected ? 3 : 2;
    
    if (node.type === 'task') {
      // Draw square for task
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
    
    // Truncate long labels
    let displayLabel = node.label;
    const maxWidth = scaledWidth * 0.8;
    const textWidth = ctx.measureText(displayLabel).width;
    
    if (textWidth > maxWidth) {
      while (ctx.measureText(displayLabel + '...').width > maxWidth && displayLabel.length > 0) {
        displayLabel = displayLabel.slice(0, -1);
      }
      displayLabel += '...';
    }
    
    ctx.fillText(displayLabel, centerX, centerY);
  }, [viewport, worldToScreen]);

  // Draw an edge
  const drawEdge = useCallback((ctx: CanvasRenderingContext2D, edge: CanvasEdge) => {
    const fromNode = nodes.find(n => n.id === edge.fromNodeId);
    const toNode = nodes.find(n => n.id === edge.toNodeId);
    
    if (!fromNode || !toNode) return;
    
    const { fromX, fromY, toX, toY } = getNodeConnectionPoint(fromNode, toNode);
    const fromScreen = worldToScreen(fromX, fromY);
    const toScreen = worldToScreen(toX, toY);
    
    ctx.strokeStyle = edge.selected ? '#2196f3' : '#666666';
    ctx.lineWidth = edge.selected ? 3 : 2;
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(fromScreen.x, fromScreen.y);
    ctx.lineTo(toScreen.x, toScreen.y);
    ctx.stroke();
    
    // Draw arrowhead
    const angle = Math.atan2(toScreen.y - fromScreen.y, toScreen.x - fromScreen.x);
    const arrowLength = 15 * viewport.zoom;
    const arrowAngle = Math.PI / 6;
    
    ctx.beginPath();
    ctx.moveTo(toScreen.x, toScreen.y);
    ctx.lineTo(
      toScreen.x - arrowLength * Math.cos(angle - arrowAngle),
      toScreen.y - arrowLength * Math.sin(angle - arrowAngle)
    );
    ctx.moveTo(toScreen.x, toScreen.y);
    ctx.lineTo(
      toScreen.x - arrowLength * Math.cos(angle + arrowAngle),
      toScreen.y - arrowLength * Math.sin(angle + arrowAngle)
    );
    ctx.stroke();
  }, [nodes, viewport, worldToScreen, getNodeConnectionPoint]);

  // Render a single tile to its cached canvas
  const renderTile = useCallback((tile: Tile): HTMLCanvasElement => {
    if (tile.canvas && !tile.isDirty) {
      return tile.canvas;
    }
    
    // Create or reuse tile canvas
    if (!tile.canvas) {
      tile.canvas = document.createElement('canvas');
      tile.canvas.width = TILE_SIZE;
      tile.canvas.height = TILE_SIZE;
    }
    
    const ctx = tile.canvas.getContext('2d')!;
    ctx.clearRect(0, 0, TILE_SIZE, TILE_SIZE);
    
    // Set up coordinate system for this tile
    ctx.save();
    ctx.translate(-tile.worldX, -tile.worldY);
    
    // Draw edges in this tile
    tile.edges.forEach(edgeId => {
      const edge = edges.find(e => e.id === edgeId);
      if (edge) {
        drawEdge(ctx, edge);
      }
    });
    
    // Draw nodes in this tile
    tile.nodes.forEach(nodeId => {
      const node = nodes.find(n => n.id === nodeId);
      if (node) {
        drawNode(ctx, node);
      }
    });
    
    ctx.restore();
    tile.isDirty = false;
    
    return tile.canvas;
  }, [edges, nodes, drawEdge, drawNode]);

  // Throttled render function for 60fps performance
  const requestRender = useCallback(() => {
    if (renderRequested) return;
    
    setRenderRequested(true);
    
    if (renderTimeoutRef.current) {
      cancelAnimationFrame(renderTimeoutRef.current);
    }
    
    renderTimeoutRef.current = requestAnimationFrame(() => {
      const now = performance.now();
      if (now - lastRenderTime < RENDER_THROTTLE_MS) {
        // Too soon, schedule for later
        renderTimeoutRef.current = requestAnimationFrame(() => {
          performTiledRender();
          setLastRenderTime(performance.now());
          setRenderRequested(false);
        });
      } else {
        performTiledRender();
        setLastRenderTime(now);
        setRenderRequested(false);
      }
    });
  }, [lastRenderTime, renderRequested]);

  // Main tiled rendering function
  const performTiledRender = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Enable image smoothing for better quality
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    
    // Draw grid background
    drawGrid(ctx, canvas);
    
    // Get visible tiles and render them
    const visibleTiles = getVisibleTiles();
    
    visibleTiles.forEach(tile => {
      const tileCanvas = renderTile(tile);
      
      // Calculate screen position for this tile
      const screenX = tile.worldX * viewport.zoom + viewport.x;
      const screenY = tile.worldY * viewport.zoom + viewport.y;
      const scaledSize = TILE_SIZE * viewport.zoom;
      
      // Draw the tile to the main canvas
      ctx.drawImage(
        tileCanvas,
        0, 0, TILE_SIZE, TILE_SIZE, // Source rectangle
        screenX, screenY, scaledSize, scaledSize // Destination rectangle
      );
    });
    
    // Draw edge being created (not part of tiles)
    if (isDrawingEdge && edgeStart) {
      ctx.strokeStyle = '#2196f3';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      
      ctx.beginPath();
      ctx.moveTo(edgeStart.x, edgeStart.y);
      ctx.lineTo(mousePos.x, mousePos.y);
      ctx.stroke();
      
      ctx.setLineDash([]);
    }
  }, [drawGrid, getVisibleTiles, renderTile, viewport, isDrawingEdge, edgeStart, mousePos]);

  // Handle canvas resize with optimized rendering
  const resizeCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    
    const rect = container.getBoundingClientRect();
    const devicePixelRatio = window.devicePixelRatio || 1;
    
    // Set actual size in memory (scaled for high DPI displays)
    canvas.width = rect.width * devicePixelRatio;
    canvas.height = rect.height * devicePixelRatio;
    
    // Scale the canvas back down using CSS
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    
    // Scale the drawing context so everything draws at the correct size
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.scale(devicePixelRatio, devicePixelRatio);
    }
    
    requestRender();
  }, [requestRender]);

  // Set up canvas and resize handling
  useEffect(() => {
    resizeCanvas();
    
    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (renderTimeoutRef.current) {
        cancelAnimationFrame(renderTimeoutRef.current);
      }
    };
  }, [resizeCanvas]);

  // Request render when dependencies change
  useEffect(() => {
    requestRender();
  }, [requestRender, tileSystem, viewport, isDrawingEdge, edgeStart, mousePos]);

  // Find node at position
  const getNodeAtPosition = useCallback((x: number, y: number): CanvasNode | null => {
    const worldPos = screenToWorld(x, y);
    
    for (let i = nodes.length - 1; i >= 0; i--) {
      const node = nodes[i];
      if (worldPos.x >= node.x && worldPos.x <= node.x + node.width &&
          worldPos.y >= node.y && worldPos.y <= node.y + node.height) {
        return node;
      }
    }
    return null;
  }, [nodes, screenToWorld]);

  // Find edge at position
  const getEdgeAtPosition = useCallback((x: number, y: number): CanvasEdge | null => {
    const threshold = 10; // pixels
    
    for (const edge of edges) {
      const fromNode = nodes.find(n => n.id === edge.fromNodeId);
      const toNode = nodes.find(n => n.id === edge.toNodeId);
      
      if (!fromNode || !toNode) continue;
      
      const { fromX, fromY, toX, toY } = getNodeConnectionPoint(fromNode, toNode);
      const fromScreen = worldToScreen(fromX, fromY);
      const toScreen = worldToScreen(toX, toY);
      
      // Calculate distance from point to line segment
      const A = x - fromScreen.x;
      const B = y - fromScreen.y;
      const C = toScreen.x - fromScreen.x;
      const D = toScreen.y - fromScreen.y;
      
      const dot = A * C + B * D;
      const lenSq = C * C + D * D;
      
      if (lenSq === 0) continue;
      
      const param = dot / lenSq;
      
      let xx, yy;
      if (param < 0) {
        xx = fromScreen.x;
        yy = fromScreen.y;
      } else if (param > 1) {
        xx = toScreen.x;
        yy = toScreen.y;
      } else {
        xx = fromScreen.x + param * C;
        yy = fromScreen.y + param * D;
      }
      
      const dx = x - xx;
      const dy = y - yy;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance <= threshold) {
        return edge;
      }
    }
    
    return null;
  }, [edges, nodes, getNodeConnectionPoint, worldToScreen]);

  // Handle mouse down
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const worldPos = screenToWorld(x, y);
    
    const clickedNode = getNodeAtPosition(x, y);
    
    if (selectedTool === 'select') {
      if (clickedNode) {
        // Select node and start dragging
        setNodes(prev => prev.map(n => ({ ...n, selected: n.id === clickedNode.id })));
        setEdges(prev => prev.map(e => ({ ...e, selected: false })));
        setDraggedNode(clickedNode.id);
        onNodeSelect?.(clickedNode.id);
      } else {
        // Check for edge selection
        const clickedEdge = getEdgeAtPosition(x, y);
        if (clickedEdge) {
          // Select edge
          setEdges(prev => prev.map(e => ({ ...e, selected: e.id === clickedEdge.id })));
          setNodes(prev => prev.map(n => ({ ...n, selected: false })));
        } else {
          // Clear selection and start panning
          setNodes(prev => prev.map(n => ({ ...n, selected: false })));
          setEdges(prev => prev.map(e => ({ ...e, selected: false })));
          setIsDragging(true);
          setDragStart({ x, y });
        }
      }
    } else if (selectedTool === 'task' || selectedTool === 'plan') {
      if (!clickedNode) {
        // Create new node
        const nodeSize = selectedTool === 'task' ? NODE_TASK_SIZE : NODE_PLAN_SIZE;
        const newNode: Omit<CanvasNode, 'id' | 'selected'> = {
          type: selectedTool,
          x: worldPos.x - nodeSize.width / 2,
          y: worldPos.y - nodeSize.height / 2,
          width: nodeSize.width,
          height: nodeSize.height,
          label: `New ${selectedTool}`
        };
        onNodeCreate?.(newNode);
      }
    } else if (selectedTool === 'edge') {
      if (clickedNode) {
        // Start edge creation
        setIsDrawingEdge(true);
        const screenPos = worldToScreen(
          clickedNode.x + clickedNode.width / 2,
          clickedNode.y + clickedNode.height / 2
        );
        setEdgeStart({ nodeId: clickedNode.id, x: screenPos.x, y: screenPos.y });
      }
    }
  }, [selectedTool, screenToWorld, getNodeAtPosition, getEdgeAtPosition, onNodeSelect, onNodeCreate, worldToScreen]);

  // Optimized mouse move handler with tiled rendering
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setMousePos({ x, y });
    
    if (isDragging && !draggedNode) {
      // Pan viewport
      const dx = x - dragStart.x;
      const dy = y - dragStart.y;
      setViewport(prev => ({
        ...prev,
        x: prev.x + dx,
        y: prev.y + dy
      }));
      setDragStart({ x, y });
      requestRender();
    } else if (draggedNode) {
      // Move node and update tiles
      const worldPos = screenToWorld(x, y);
      const oldNode = nodes.find(n => n.id === draggedNode);
      
      if (oldNode) {
        // Remove from old tiles
        removeNodeFromTiles(draggedNode);
        
        // Update node position
        const updatedNode = { 
          ...oldNode, 
          x: worldPos.x - oldNode.width / 2, 
          y: worldPos.y - oldNode.height / 2 
        };
        
        setNodes(prev => prev.map(n => 
          n.id === draggedNode ? updatedNode : n
        ));
        
        // Add to new tiles
        addNodeToTiles(updatedNode);
        
        // Update edges that connect to this node
        edges.forEach(edge => {
          if (edge.fromNodeId === draggedNode || edge.toNodeId === draggedNode) {
            removeEdgeFromTiles(edge.id);
            addEdgeToTiles(edge);
          }
        });
      }
      
      requestRender();
    } else if (isDrawingEdge) {
      requestRender();
    }
  }, [isDragging, draggedNode, dragStart, screenToWorld, isDrawingEdge, requestRender, nodes, edges, removeNodeFromTiles, addNodeToTiles, removeEdgeFromTiles, addEdgeToTiles]);

  // Handle mouse up
  const handleMouseUp = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (draggedNode) {
      // Finish node move
      const node = nodes.find(n => n.id === draggedNode);
      if (node) {
        onNodeMove?.(draggedNode, node.x, node.y);
      }
      setDraggedNode(null);
    }
    
    if (isDrawingEdge && edgeStart) {
      // Finish edge creation
      const targetNode = getNodeAtPosition(x, y);
      if (targetNode && targetNode.id !== edgeStart.nodeId) {
        const newEdge: Omit<CanvasEdge, 'id' | 'selected'> = {
          fromNodeId: edgeStart.nodeId,
          toNodeId: targetNode.id
        };
        onEdgeCreate?.(newEdge);
      }
      setIsDrawingEdge(false);
      setEdgeStart(null);
    }
    
    setIsDragging(false);
  }, [draggedNode, nodes, onNodeMove, isDrawingEdge, edgeStart, getNodeAtPosition, onEdgeCreate]);

  // Optimized wheel handler for smooth zooming
  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Smooth zoom with variable speed based on current zoom level
    const zoomSpeed = viewport.zoom > 1 ? 0.95 : 0.9;
    const zoomFactor = e.deltaY > 0 ? zoomSpeed : (1 / zoomSpeed);
    const newZoom = Math.max(0.05, Math.min(5, viewport.zoom * zoomFactor));
    
    // Zoom towards mouse position with smooth interpolation
    const worldPos = screenToWorld(x, y);
    const newViewport = {
      x: x - worldPos.x * newZoom,
      y: y - worldPos.y * newZoom,
      zoom: newZoom
    };
    
    setViewport(newViewport);
    requestRender();
  }, [viewport, screenToWorld, requestRender]);

  // Handle key presses for deletion with tile cleanup
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const selectedNode = nodes.find(n => n.selected);
        const selectedEdge = edges.find(e => e.selected);
        
        if (selectedNode) {
          // Clean up tiles before deleting node
          removeNodeFromTiles(selectedNode.id);
          onNodeDelete?.(selectedNode.id);
        } else if (selectedEdge) {
          // Clean up tiles before deleting edge
          removeEdgeFromTiles(selectedEdge.id);
          onEdgeDelete?.(selectedEdge.id);
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nodes, edges, onNodeDelete, onEdgeDelete, removeNodeFromTiles, removeEdgeFromTiles]);

  const handleRefreshValidation = useCallback(() => {
    if (graph && showValidation) {
      // Use server-side validation for manual refresh to get latest business rules
      validateGraph(graph, true);
    }
  }, [graph, showValidation, validateGraph]);

  // Cleanup tiling system on unmount
  useEffect(() => {
    return () => {
      // Clean up tile canvases to prevent memory leaks
      tileSystem.tiles.forEach(tile => {
        if (tile.canvas) {
          tile.canvas.width = 0;
          tile.canvas.height = 0;
        }
      });
      
      if (renderTimeoutRef.current) {
        cancelAnimationFrame(renderTimeoutRef.current);
      }
    };
  }, [tileSystem.tiles]);

  return (
    <div className="graph-canvas">
      <div className="canvas-toolbar">
        <div className="toolbar-group">
          <button 
            className={`tool-button ${selectedTool === 'select' ? 'active' : ''}`}
            onClick={() => onToolChange('select')}
          >
            ↖️ Select
          </button>
          <button 
            className={`tool-button ${selectedTool === 'task' ? 'active' : ''}`}
            onClick={() => onToolChange('task')}
          >
            📦 Task
          </button>
          <button 
            className={`tool-button ${selectedTool === 'plan' ? 'active' : ''}`}
            onClick={() => onToolChange('plan')}
          >
            ⭕ Plan
          </button>
          <button 
            className={`tool-button ${selectedTool === 'edge' ? 'active' : ''}`}
            onClick={() => onToolChange('edge')}
          >
            ↗️ Edge
          </button>
        </div>
        
        {showValidation && (
          <div className="validation-toolbar">
            <ValidationStatusBar
              validationResult={validationState.lastValidationResult}
              isValidating={validationState.isValidating}
              onRefreshValidation={handleRefreshValidation}
              className="compact"
            />
          </div>
        )}
      </div>
      
      <div className="canvas-content" ref={containerRef}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          style={{ cursor: selectedTool === 'select' ? 'default' : 'crosshair' }}
        />
        
        {showValidation && (
          <ValidationOverlay
            validationResult={validationState.lastValidationResult}
            isVisible={showValidationOverlay}
            position={validationOverlayPosition}
          />
        )}
      </div>
    </div>
  );
};

export default GraphCanvas;