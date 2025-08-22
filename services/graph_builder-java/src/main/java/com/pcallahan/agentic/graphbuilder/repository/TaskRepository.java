package com.pcallahan.agentic.graphbuilder.repository;

import com.pcallahan.agentic.graphbuilder.entity.TaskEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository interface for TaskEntity operations.
 */
@Repository
public interface TaskRepository extends JpaRepository<TaskEntity, String> {

    /**
     * Find all tasks for a specific agent graph.
     */
    List<TaskEntity> findByAgentGraphId(String graphId);

    /**
     * Find a task by graph ID and task name.
     */
    Optional<TaskEntity> findByAgentGraphIdAndTaskName(String graphId, String taskName);

    /**
     * Find all tasks for a specific upstream plan.
     */
    List<TaskEntity> findByUpstreamPlanId(String planId);

    /**
     * Delete all tasks for a specific agent graph.
     */
    void deleteByAgentGraphId(String graphId);
}