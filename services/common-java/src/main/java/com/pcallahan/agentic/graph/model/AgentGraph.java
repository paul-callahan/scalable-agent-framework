package com.pcallahan.agentic.graph.model;

import java.util.Collections;
import java.util.Map;
import java.util.Set;

/**
 * Represents a complete agent graph specification.
 * 
 * <p>An agent graph defines the structure and relationships between plans and tasks
 * in the scalable agent framework. The graph consists of:</p>
 * <ul>
 *   <li>Plans: Nodes that process task results and produce plan results</li>
 *   <li>Tasks: Nodes that process plan results and produce task results</li>
 *   <li>Relationships: Directed edges defining data flow between nodes</li>
 * </ul>
 * 
 * <p>The graph enforces the constraint that tasks can only have one upstream plan,
 * while plans can have multiple upstream tasks and multiple downstream tasks.</p>
 * 
 * @param plans Map of plan names to Plan objects
 * @param tasks Map of task names to Task objects
 * @param planToTasks Map of plan names to sets of downstream task names
 * @param taskToPlan Map of task names to their upstream plan name
 */
public record AgentGraph(
    Map<String, Plan> plans,
    Map<String, Task> tasks,
    Map<String, Set<String>> planToTasks,
    Map<String, String> taskToPlan
) {
    
    /**
     * Compact constructor with validation and defensive copying.
     * 
     * @param plans The plans map
     * @param tasks The tasks map
     * @param planToTasks The plan-to-tasks mapping
     * @param taskToPlan The task-to-plan mapping
     * @throws IllegalArgumentException if validation fails
     */
    public AgentGraph {
        if (plans == null) {
            throw new IllegalArgumentException("Plans map cannot be null");
        }
        if (tasks == null) {
            throw new IllegalArgumentException("Tasks map cannot be null");
        }
        if (planToTasks == null) {
            throw new IllegalArgumentException("Plan-to-tasks mapping cannot be null");
        }
        if (taskToPlan == null) {
            throw new IllegalArgumentException("Task-to-plan mapping cannot be null");
        }
        
        // Create defensive copies for immutability
        plans = Map.copyOf(plans);
        tasks = Map.copyOf(tasks);
        planToTasks = Map.copyOf(planToTasks);
        taskToPlan = Map.copyOf(taskToPlan);
    }
    
    /**
     * Creates a new AgentGraph with the specified components.
     * 
     * @param plans The plans map
     * @param tasks The tasks map
     * @param planToTasks The plan-to-tasks mapping
     * @param taskToPlan The task-to-plan mapping
     * @return A new AgentGraph
     */
    public static AgentGraph of(
        Map<String, Plan> plans,
        Map<String, Task> tasks,
        Map<String, Set<String>> planToTasks,
        Map<String, String> taskToPlan
    ) {
        return new AgentGraph(plans, tasks, planToTasks, taskToPlan);
    }
    
    /**
     * Creates an empty AgentGraph.
     * 
     * @return An empty AgentGraph
     */
    public static AgentGraph empty() {
        return new AgentGraph(Map.of(), Map.of(), Map.of(), Map.of());
    }
    
    /**
     * Gets a plan by name.
     * 
     * @param name The plan name
     * @return The Plan, or null if not found
     */
    public Plan getPlan(String name) {
        return plans.get(name);
    }
    
    /**
     * Gets a task by name.
     * 
     * @param name The task name
     * @return The Task, or null if not found
     */
    public Task getTask(String name) {
        return tasks.get(name);
    }
    
    /**
     * Gets the downstream tasks for a plan.
     * 
     * @param planName The plan name
     * @return Set of downstream task names, or empty set if not found
     */
    public Set<String> getDownstreamTasks(String planName) {
        return planToTasks.getOrDefault(planName, Set.of());
    }
    
    /**
     * Gets the upstream plan for a task.
     * 
     * @param taskName The task name
     * @return The upstream plan name, or null if not found
     */
    public String getUpstreamPlan(String taskName) {
        return taskToPlan.get(taskName);
    }
    
    /**
     * Gets all plan names.
     * 
     * @return Set of all plan names
     */
    public Set<String> getAllPlanNames() {
        return plans.keySet();
    }
    
    /**
     * Gets all task names.
     * 
     * @return Set of all task names
     */
    public Set<String> getAllTaskNames() {
        return tasks.keySet();
    }
    
    /**
     * Checks if the graph is empty.
     * 
     * @return true if the graph has no plans or tasks
     */
    public boolean isEmpty() {
        return plans.isEmpty() && tasks.isEmpty();
    }
    
    /**
     * Gets the number of plans in the graph.
     * 
     * @return The number of plans
     */
    public int planCount() {
        return plans.size();
    }
    
    /**
     * Gets the number of tasks in the graph.
     * 
     * @return The number of tasks
     */
    public int taskCount() {
        return tasks.size();
    }
    
    /**
     * Gets the total number of nodes in the graph.
     * 
     * @return The total number of plans and tasks
     */
    public int totalNodeCount() {
        return plans.size() + tasks.size();
    }
} 