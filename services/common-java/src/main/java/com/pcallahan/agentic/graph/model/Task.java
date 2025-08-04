package com.pcallahan.agentic.graph.model;

import java.nio.file.Path;

/**
 * Represents a task in the agent graph specification.
 * 
 * <p>A task is a node in the agent graph that processes results from a single upstream plan
 * and produces a task result that can be consumed by downstream plans. Each task has a unique
 * name and is associated with a Python subproject directory containing the task implementation.</p>
 * 
 * <p>The task's Python subproject should contain:</p>
 * <ul>
 *   <li>A {@code task.py} file with a {@code execute(upstream_plan: PlanResult) -> TaskResult} function</li>
 *   <li>A {@code requirements.txt} file listing dependencies</li>
 * </ul>
 * 
 * <p>Tasks can only have one upstream plan (enforcing the constraint that tasks process
 * single plan results), but can feed into multiple downstream plans.</p>
 * 
 * @param name The unique identifier for this task
 * @param label The human-readable label for this task
 * @param taskSource Path to the Python subproject directory containing the task implementation
 * @param upstreamPlanId ID of the single plan that feeds into this task
 */
public record Task(String name, String label, Path taskSource, String upstreamPlanId) {
    
    /**
     * Compact constructor with validation.
     * 
     * @param name The task name
     * @param taskSource The task source directory
     * @param upstreamPlanId The upstream plan ID
     * @throws IllegalArgumentException if validation fails
     */
    public Task {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Task name cannot be null or empty");
        }
        if (taskSource == null) {
            throw new IllegalArgumentException("Task source cannot be null");
        }
        if (upstreamPlanId == null || upstreamPlanId.trim().isEmpty()) {
            throw new IllegalArgumentException("Upstream plan ID cannot be null or empty");
        }
    }
    
    /**
     * Creates a new Task with the specified name, source directory, and upstream plan.
     * 
     * @param name The task name
     * @param taskSource The task source directory
     * @param upstreamPlanId The upstream plan ID
     * @return A new Task
     */
    public static Task of(String name, Path taskSource, String upstreamPlanId) {
        return new Task(name, name, taskSource, upstreamPlanId);
    }
} 