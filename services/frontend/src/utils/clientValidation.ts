import type { AgentGraphDto, ValidationResult } from '../types';

// Python identifier pattern: starts with letter or underscore, followed by letters, digits, or underscores
const PYTHON_IDENTIFIER_PATTERN = /^[a-zA-Z_][a-zA-Z0-9_]*$/;

// Python keywords that cannot be used as identifiers
const PYTHON_KEYWORDS = new Set([
  'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
  'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
  'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass',
  'raise', 'return', 'try', 'while', 'with', 'yield'
]);

/**
 * Client-side validation utilities for graph composer
 * These handle most validation cases without requiring API calls
 */
export class ClientValidation {
  
  /**
   * Validate a Python identifier (node name)
   */
  static validatePythonIdentifier(nodeName: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!nodeName || nodeName.trim().length === 0) {
      errors.push('Node name cannot be empty');
      return { valid: false, errors, warnings };
    }
    
    const trimmedName = nodeName.trim();
    
    // Check if it matches Python identifier pattern
    if (!PYTHON_IDENTIFIER_PATTERN.test(trimmedName)) {
      errors.push(
        `Node name '${trimmedName}' is not a valid Python identifier. ` +
        'It must start with a letter or underscore and contain only letters, digits, and underscores.'
      );
    }
    
    // Check if it's a Python keyword
    if (PYTHON_KEYWORDS.has(trimmedName)) {
      errors.push(`Node name '${trimmedName}' is a Python keyword and cannot be used as an identifier`);
    }
    
    // Warn about naming conventions
    if (trimmedName.startsWith('_')) {
      warnings.push(`Node name '${trimmedName}' starts with underscore, which is typically reserved for internal use`);
    }
    
    if (trimmedName.toUpperCase() === trimmedName && trimmedName.length > 1) {
      warnings.push(`Node name '${trimmedName}' is all uppercase, which is typically reserved for constants`);
    }
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Validate node name uniqueness within existing names
   */
  static validateNodeNameUniqueness(
    nodeName: string,
    existingNodeNames: string[],
    excludeNodeId?: string
  ): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!nodeName || nodeName.trim().length === 0) {
      errors.push('Node name cannot be empty');
      return { valid: false, errors, warnings };
    }
    
    const trimmedName = nodeName.trim();
    
    // Filter out the excluded node if provided
    const relevantNames = excludeNodeId 
      ? existingNodeNames.filter(name => name !== excludeNodeId)
      : existingNodeNames;
    
    if (relevantNames.includes(trimmedName)) {
      errors.push(`Node name '${trimmedName}' already exists in the graph`);
    }
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Comprehensive node name validation combining identifier and uniqueness checks
   */
  static validateNodeName(
    nodeName: string,
    existingNodeNames: string[] = [],
    excludeNodeId?: string
  ): ValidationResult {
    // First validate Python identifier format
    const identifierResult = this.validatePythonIdentifier(nodeName);
    if (!identifierResult.valid) {
      return identifierResult;
    }
    
    // Then validate uniqueness
    const uniquenessResult = this.validateNodeNameUniqueness(nodeName, existingNodeNames, excludeNodeId);
    
    // Combine results
    return {
      valid: identifierResult.valid && uniquenessResult.valid,
      errors: [...identifierResult.errors, ...uniquenessResult.errors],
      warnings: [...identifierResult.warnings, ...uniquenessResult.warnings]
    };
  }
  
  /**
   * Validate connection constraints (plans only connect to tasks, tasks only to plans)
   */
  static validateConnectionConstraints(graph: AgentGraphDto): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const planNames = new Set(graph.plans?.map(p => p.name) || []);
    const taskNames = new Set(graph.tasks?.map(t => t.name) || []);
    
    // Validate plan-to-task connections
    if (graph.planToTasks) {
      for (const [planName, connectedNodes] of Object.entries(graph.planToTasks)) {
        if (!planNames.has(planName)) {
          errors.push(`Plan '${planName}' referenced in connections but not found in graph`);
          continue;
        }
        
        for (const connectedNode of connectedNodes) {
          if (!taskNames.has(connectedNode)) {
            errors.push(`Plan '${planName}' is connected to '${connectedNode}' which is not a task`);
          }
        }
      }
    }
    
    // Validate task-to-plan connections
    if (graph.taskToPlan) {
      for (const [taskName, connectedPlan] of Object.entries(graph.taskToPlan)) {
        if (!taskNames.has(taskName)) {
          errors.push(`Task '${taskName}' referenced in connections but not found in graph`);
          continue;
        }
        
        if (!planNames.has(connectedPlan)) {
          errors.push(`Task '${taskName}' is connected to '${connectedPlan}' which is not a plan`);
        }
      }
    }
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Validate that each task has exactly one upstream plan
   */
  static validateTaskUpstreamConstraints(graph: AgentGraphDto): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const planNames = new Set(graph.plans?.map(p => p.name) || []);
    
    if (graph.tasks && graph.taskToPlan) {
      for (const task of graph.tasks) {
        const upstreamPlan = graph.taskToPlan[task.name];
        
        if (!upstreamPlan) {
          errors.push(`Task '${task.name}' must have exactly one upstream plan`);
        } else if (!planNames.has(upstreamPlan)) {
          errors.push(`Task '${task.name}' references upstream plan '${upstreamPlan}' which does not exist`);
        }
      }
    }
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Validate plan upstream constraints
   */
  static validatePlanUpstreamConstraints(graph: AgentGraphDto): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const taskNames = new Set(graph.tasks?.map(t => t.name) || []);
    
    if (graph.plans) {
      for (const plan of graph.plans) {
        if (plan.upstreamTaskIds) {
          for (const upstreamTaskId of plan.upstreamTaskIds) {
            if (!taskNames.has(upstreamTaskId)) {
              errors.push(`Plan '${plan.name}' references upstream task '${upstreamTaskId}' which does not exist`);
            }
          }
        }
      }
    }
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Validate graph connectivity and find orphaned nodes
   */
  static validateConnectivity(graph: AgentGraphDto): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const allNodes = new Set<string>();
    const connectedNodes = new Set<string>();
    
    // Collect all node names
    graph.plans?.forEach(plan => allNodes.add(plan.name));
    graph.tasks?.forEach(task => allNodes.add(task.name));
    
    // Collect connected nodes
    if (graph.planToTasks) {
      Object.keys(graph.planToTasks).forEach(plan => connectedNodes.add(plan));
      Object.values(graph.planToTasks).forEach(tasks => 
        tasks.forEach(task => connectedNodes.add(task))
      );
    }
    
    if (graph.taskToPlan) {
      Object.keys(graph.taskToPlan).forEach(task => connectedNodes.add(task));
      Object.values(graph.taskToPlan).forEach(plan => connectedNodes.add(plan));
    }
    
    // Find orphaned nodes
    const orphanedNodes = Array.from(allNodes).filter(node => !connectedNodes.has(node));
    
    orphanedNodes.forEach(node => {
      warnings.push(`Node '${node}' is not connected to any other nodes`);
    });
    
    // Check for empty or single-node graph
    if (allNodes.size === 0) {
      warnings.push('Graph contains no nodes');
    } else if (allNodes.size === 1) {
      warnings.push('Graph contains only one node');
    }
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Validate node name uniqueness across the entire graph
   */
  static validateGraphNodeNameUniqueness(graph: AgentGraphDto): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const allNodeNames = new Set<string>();
    const duplicateNames = new Set<string>();
    
    // Check plan names
    graph.plans?.forEach(plan => {
      if (plan.name) {
        if (allNodeNames.has(plan.name)) {
          duplicateNames.add(plan.name);
        } else {
          allNodeNames.add(plan.name);
        }
      }
    });
    
    // Check task names
    graph.tasks?.forEach(task => {
      if (task.name) {
        if (allNodeNames.has(task.name)) {
          duplicateNames.add(task.name);
        } else {
          allNodeNames.add(task.name);
        }
      }
    });
    
    // Report duplicates
    duplicateNames.forEach(name => {
      errors.push(`Node name '${name}' is used multiple times in the graph`);
    });
    
    return { valid: errors.length === 0, errors, warnings };
  }
  
  /**
   * Comprehensive graph validation combining all checks
   */
  static validateGraph(graph: AgentGraphDto): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!graph) {
      errors.push('Graph cannot be null');
      return { valid: false, errors, warnings };
    }
    
    // Basic graph properties
    if (!graph.name || graph.name.trim().length === 0) {
      errors.push('Graph name cannot be empty');
    }
    
    if (!graph.tenantId || graph.tenantId.trim().length === 0) {
      errors.push('Tenant ID cannot be empty');
    }
    
    // Run all validation checks
    const validationChecks = [
      this.validateGraphNodeNameUniqueness(graph),
      this.validateConnectionConstraints(graph),
      this.validateTaskUpstreamConstraints(graph),
      this.validatePlanUpstreamConstraints(graph),
      this.validateConnectivity(graph)
    ];
    
    // Combine all results
    validationChecks.forEach(result => {
      errors.push(...result.errors);
      warnings.push(...result.warnings);
    });
    
    return { valid: errors.length === 0, errors, warnings };
  }
}