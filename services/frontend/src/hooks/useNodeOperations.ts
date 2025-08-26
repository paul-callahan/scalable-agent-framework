import { useCallback } from 'react';
import { useAppContext } from './useAppContext';
import { useGraphs } from './useGraphs';
import { useValidation } from './useValidation';
import { createDefaultFilesForPlan, createDefaultFilesForTask } from '../utils/templateGenerator';
import type { AgentGraphDto, PlanDto, TaskDto } from '../types';

export function useNodeOperations() {
  const { state, dispatch } = useAppContext();
  const { updateGraph } = useGraphs();
  const { validateNodeName, validateGraph } = useValidation();

  const addPlanNode = useCallback(async (planName: string, label?: string) => {
    if (!state.currentGraph) {
      throw new Error('No graph loaded');
    }

    // Validate node name
    const existingNodeNames = [
      ...state.currentGraph.plans.map(p => p.name),
      ...state.currentGraph.tasks.map(t => t.name)
    ];
    
    const validationResult = await validateNodeName(
      planName,
      state.currentGraph.id,
      existingNodeNames
    );
    
    if (!validationResult.valid) {
      throw new Error(validationResult.errors.join(', '));
    }

    // Create new plan with default files
    const newPlan: PlanDto = {
      name: planName,
      label: label || planName,
      upstreamTaskIds: [],
      files: createDefaultFilesForPlan(planName)
    };

    // Update the graph
    const updatedGraph: AgentGraphDto = {
      ...state.currentGraph,
      plans: [...state.currentGraph.plans, newPlan],
      updatedAt: new Date().toISOString()
    };

    try {
      await updateGraph(state.currentGraph.id, updatedGraph);
      return newPlan;
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to add plan node'
      });
      throw error;
    }
  }, [state.currentGraph, updateGraph, dispatch, validateNodeName]);

  const addTaskNode = useCallback(async (taskName: string, label?: string, upstreamPlanId?: string) => {
    if (!state.currentGraph) {
      throw new Error('No graph loaded');
    }

    // Validate node name
    const existingNodeNames = [
      ...state.currentGraph.plans.map(p => p.name),
      ...state.currentGraph.tasks.map(t => t.name)
    ];
    
    const validationResult = await validateNodeName(
      taskName,
      state.currentGraph.id,
      existingNodeNames
    );
    
    if (!validationResult.valid) {
      throw new Error(validationResult.errors.join(', '));
    }

    // Create new task with default files
    const newTask: TaskDto = {
      name: taskName,
      label: label || taskName,
      upstreamPlanId: upstreamPlanId || '',
      files: createDefaultFilesForTask(taskName)
    };

    // Update the graph
    const updatedGraph: AgentGraphDto = {
      ...state.currentGraph,
      tasks: [...state.currentGraph.tasks, newTask],
      updatedAt: new Date().toISOString()
    };

    // Update taskToPlan mapping if upstreamPlanId is provided
    if (upstreamPlanId) {
      updatedGraph.taskToPlan = {
        ...updatedGraph.taskToPlan,
        [taskName]: upstreamPlanId
      };
    }

    try {
      await updateGraph(state.currentGraph.id, updatedGraph);
      return newTask;
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to add task node'
      });
      throw error;
    }
  }, [state.currentGraph, updateGraph, dispatch, validateNodeName]);

  const removeNode = useCallback(async (nodeId: string, nodeType: 'plan' | 'task') => {
    if (!state.currentGraph) {
      throw new Error('No graph loaded');
    }

    let updatedGraph: AgentGraphDto;

    if (nodeType === 'plan') {
      // Remove plan and update related mappings
      updatedGraph = {
        ...state.currentGraph,
        plans: state.currentGraph.plans.filter(p => p.name !== nodeId),
        planToTasks: Object.fromEntries(
          Object.entries(state.currentGraph.planToTasks).filter(([planId]) => planId !== nodeId)
        ),
        taskToPlan: Object.fromEntries(
          Object.entries(state.currentGraph.taskToPlan).filter(([, planId]) => planId !== nodeId)
        ),
        updatedAt: new Date().toISOString()
      };
    } else {
      // Remove task and update related mappings
      updatedGraph = {
        ...state.currentGraph,
        tasks: state.currentGraph.tasks.filter(t => t.name !== nodeId),
        taskToPlan: Object.fromEntries(
          Object.entries(state.currentGraph.taskToPlan).filter(([taskId]) => taskId !== nodeId)
        ),
        planToTasks: Object.fromEntries(
          Object.entries(state.currentGraph.planToTasks).map(([planId, taskIds]) => [
            planId,
            taskIds.filter(taskId => taskId !== nodeId)
          ])
        ),
        updatedAt: new Date().toISOString()
      };
    }

    try {
      await updateGraph(state.currentGraph.id, updatedGraph);
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to remove node'
      });
      throw error;
    }
  }, [state.currentGraph, updateGraph, dispatch]);

  const connectNodes = useCallback(async (fromNodeId: string, toNodeId: string, fromType: 'plan' | 'task', toType: 'plan' | 'task') => {
    if (!state.currentGraph) {
      throw new Error('No graph loaded');
    }

    // Validate connection rules: plans connect to tasks, tasks connect to plans
    if (fromType === toType) {
      throw new Error('Cannot connect nodes of the same type');
    }

    let updatedGraph = { ...state.currentGraph };

    if (fromType === 'plan' && toType === 'task') {
      // Plan to Task connection
      const currentTasks = updatedGraph.planToTasks[fromNodeId] || [];
      updatedGraph.planToTasks = {
        ...updatedGraph.planToTasks,
        [fromNodeId]: [...currentTasks, toNodeId]
      };
      updatedGraph.taskToPlan = {
        ...updatedGraph.taskToPlan,
        [toNodeId]: fromNodeId
      };
      
      // Update the task's upstreamPlanId
      updatedGraph.tasks = updatedGraph.tasks.map(task => 
        task.name === toNodeId ? { ...task, upstreamPlanId: fromNodeId } : task
      );
    } else if (fromType === 'task' && toType === 'plan') {
      // Task to Plan connection
      const currentTasks = updatedGraph.planToTasks[toNodeId] || [];
      updatedGraph.planToTasks = {
        ...updatedGraph.planToTasks,
        [toNodeId]: [...currentTasks, fromNodeId]
      };
      
      // Update the plan's upstreamTaskIds
      updatedGraph.plans = updatedGraph.plans.map(plan => 
        plan.name === toNodeId 
          ? { ...plan, upstreamTaskIds: [...plan.upstreamTaskIds, fromNodeId] }
          : plan
      );
    }

    updatedGraph.updatedAt = new Date().toISOString();

    // Validate the updated graph
    const graphValidationResult = await validateGraph(updatedGraph);
    if (!graphValidationResult.valid) {
      throw new Error(`Connection validation failed: ${graphValidationResult.errors.join(', ')}`);
    }

    try {
      await updateGraph(state.currentGraph.id, updatedGraph);
    } catch (error) {
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to connect nodes'
      });
      throw error;
    }
  }, [state.currentGraph, updateGraph, dispatch, validateGraph]);

  return {
    addPlanNode,
    addTaskNode,
    removeNode,
    connectNodes
  };
}