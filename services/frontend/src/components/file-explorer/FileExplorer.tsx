import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../hooks/useAppContext';
import { useNodeOperations } from '../../hooks/useNodeOperations';
import type { ExecutorFile, PlanDto, TaskDto } from '../../types';
import './FileExplorer.css';

interface TreeNode {
  id: string;
  name: string;
  type: 'root' | 'folder' | 'file';
  children?: TreeNode[];
  file?: ExecutorFile;
  nodeId?: string; // For linking to canvas nodes
  nodeType?: 'plan' | 'task';
  expanded?: boolean;
}

const FileExplorer: React.FC = () => {
  const { state, dispatch } = useAppContext();
  const { currentGraph, selectedNodeId, selectedFile } = state;
  const { addPlanNode, addTaskNode } = useNodeOperations();
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['root', 'plans', 'tasks']));

  // Build tree structure from current graph
  const buildTreeStructure = (): TreeNode => {
    if (!currentGraph) {
      return {
        id: 'root',
        name: 'No Graph Loaded',
        type: 'root',
        children: []
      };
    }

    const plansFolder: TreeNode = {
      id: 'plans',
      name: 'plans',
      type: 'folder',
      expanded: expandedNodes.has('plans'),
      children: currentGraph.plans.map((plan: PlanDto) => ({
        id: `plan-${plan.name}`,
        name: plan.name,
        type: 'folder',
        nodeId: plan.name,
        nodeType: 'plan' as const,
        expanded: expandedNodes.has(`plan-${plan.name}`),
        children: plan.files.map((file: ExecutorFile) => ({
          id: `plan-${plan.name}-${file.name}`,
          name: file.name,
          type: 'file' as const,
          file,
          nodeId: plan.name,
          nodeType: 'plan' as const
        }))
      }))
    };

    const tasksFolder: TreeNode = {
      id: 'tasks',
      name: 'tasks',
      type: 'folder',
      expanded: expandedNodes.has('tasks'),
      children: currentGraph.tasks.map((task: TaskDto) => ({
        id: `task-${task.name}`,
        name: task.name,
        type: 'folder',
        nodeId: task.name,
        nodeType: 'task' as const,
        expanded: expandedNodes.has(`task-${task.name}`),
        children: task.files.map((file: ExecutorFile) => ({
          id: `task-${task.name}-${file.name}`,
          name: file.name,
          type: 'file' as const,
          file,
          nodeId: task.name,
          nodeType: 'task' as const
        }))
      }))
    };

    return {
      id: 'root',
      name: currentGraph.name,
      type: 'root',
      expanded: true,
      children: [plansFolder, tasksFolder]
    };
  };

  const toggleExpanded = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const handleFileSelect = (file: ExecutorFile) => {
    dispatch({ type: 'SET_SELECTED_FILE', payload: file });
  };

  const getFileIcon = (fileName: string): string => {
    if (fileName.endsWith('.py')) return '🐍';
    if (fileName === 'requirements.txt') return '📋';
    return '📄';
  };

  const getFolderIcon = (expanded: boolean): string => {
    return expanded ? '📂' : '📁';
  };

  const renderTreeNode = (node: TreeNode, depth: number = 0): React.ReactNode => {
    const isExpanded = expandedNodes.has(node.id);
    const isSelected = selectedFile?.name === node.file?.name;
    const isNodeSelected = selectedNodeId === node.nodeId;

    return (
      <div key={node.id} className="tree-node">
        <div 
          className={`tree-item ${isSelected ? 'selected' : ''} ${isNodeSelected && node.type === 'folder' ? 'node-selected' : ''}`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => {
            if (node.type === 'folder') {
              toggleExpanded(node.id);
            } else if (node.file) {
              handleFileSelect(node.file);
            }
          }}
        >
          {node.type === 'folder' && (
            <span className="expand-icon">
              {node.children && node.children.length > 0 ? (isExpanded ? '▼' : '▶') : ''}
            </span>
          )}
          <span className="icon">
            {node.type === 'root' ? '🏠' : 
             node.type === 'folder' ? getFolderIcon(isExpanded) : 
             getFileIcon(node.name)}
          </span>
          <span className="name">{node.name}</span>
        </div>
        {node.children && isExpanded && (
          <div className="tree-children">
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Auto-expand folders when a node is selected on canvas
  useEffect(() => {
    if (selectedNodeId && currentGraph) {
      const newExpanded = new Set(expandedNodes);
      
      // Find if it's a plan or task
      const plan = currentGraph.plans.find(p => p.name === selectedNodeId);
      const task = currentGraph.tasks.find(t => t.name === selectedNodeId);
      
      if (plan) {
        newExpanded.add('plans');
        newExpanded.add(`plan-${plan.name}`);
      } else if (task) {
        newExpanded.add('tasks');
        newExpanded.add(`task-${task.name}`);
      }
      
      setExpandedNodes(newExpanded);
    }
  }, [selectedNodeId, currentGraph]);

  const handleAddPlan = async () => {
    try {
      const planName = `plan_${Date.now()}`;
      await addPlanNode(planName, `Plan ${planName}`);
    } catch (error) {
      console.error('Failed to add plan:', error);
    }
  };

  const handleAddTask = async () => {
    try {
      const taskName = `task_${Date.now()}`;
      await addTaskNode(taskName, `Task ${taskName}`);
    } catch (error) {
      console.error('Failed to add task:', error);
    }
  };

  const treeStructure = buildTreeStructure();

  return (
    <div className="file-explorer">
      <div className="explorer-header">
        <h3>File Explorer</h3>
        {currentGraph && (
          <div className="demo-buttons">
            <button onClick={handleAddPlan} className="demo-button">+ Plan</button>
            <button onClick={handleAddTask} className="demo-button">+ Task</button>
          </div>
        )}
      </div>
      <div className="explorer-content">
        {renderTreeNode(treeStructure)}
      </div>
    </div>
  );
};

export default FileExplorer;