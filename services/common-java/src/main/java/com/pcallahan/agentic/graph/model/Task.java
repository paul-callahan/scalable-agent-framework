package com.pcallahan.agentic.graph.model;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

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
 * @param files List of ExecutorFile objects containing the task implementation files
 */
public record Task(String name, String label, Path taskSource, String upstreamPlanId, List<ExecutorFile> files) {
    
    /**
     * Compact constructor with validation.
     * 
     * @param name The task name
     * @param taskSource The task source directory
     * @param upstreamPlanId The upstream plan ID
     * @param files The list of ExecutorFile objects
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
        if (files == null) {
            files = new ArrayList<>();
        } else {
            files = List.copyOf(files);
        }
    }
    
    /**
     * Creates a new Task with the specified name, source directory, and upstream plan.
     * 
     * @param name The task name
     * @param taskSource The task source directory
     * @param upstreamPlanId The upstream plan ID
     * @return A new Task with no files
     */
    public static Task of(String name, Path taskSource, String upstreamPlanId) {
        return new Task(name, name, taskSource, upstreamPlanId, new ArrayList<>());
    }
    
    /**
     * Returns a new Task with the specified files.
     * 
     * @param newFiles The ExecutorFile list to set
     * @return A new Task with the specified files
     */
    public Task withFiles(List<ExecutorFile> newFiles) {
        return new Task(name, label, taskSource, upstreamPlanId, List.copyOf(newFiles));
    }
    
    /**
     * Returns a new Task with an additional file.
     * 
     * @param file The ExecutorFile to add
     * @return A new Task with the additional file
     */
    public Task withFile(ExecutorFile file) {
        List<ExecutorFile> newFiles = new ArrayList<>(files);
        newFiles.add(file);
        return new Task(name, label, taskSource, upstreamPlanId, List.copyOf(newFiles));
    }
} 