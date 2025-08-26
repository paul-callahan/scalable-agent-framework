package com.pcallahan.agentic.graph.repository;

import com.pcallahan.agentic.graph.entity.TaskEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
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
    Optional<TaskEntity> findByAgentGraphIdAndName(String graphId, String name);

    /**
     * Find all tasks for a specific upstream plan.
     */
    List<TaskEntity> findByUpstreamPlanId(String planId);

    /**
     * Delete all tasks for a specific agent graph.
     */
    void deleteByAgentGraphId(String graphId);
    
    /**
     * Find a task by ID and agent graph ID.
     */
    Optional<TaskEntity> findByIdAndAgentGraphId(String id, String graphId);

    /**
     * Find all tasks for a graph with files eagerly loaded (optimized query).
     */
    @Query("SELECT DISTINCT t FROM TaskEntity t " +
           "LEFT JOIN FETCH t.files " +
           "LEFT JOIN FETCH t.upstreamPlan " +
           "WHERE t.agentGraph.id = :graphId")
    List<TaskEntity> findByAgentGraphIdWithFiles(@Param("graphId") String graphId);

    /**
     * Find task with all relationships for detailed view.
     */
    @Query("SELECT DISTINCT t FROM TaskEntity t " +
           "LEFT JOIN FETCH t.files " +
           "LEFT JOIN FETCH t.upstreamPlan " +
           "LEFT JOIN FETCH t.downstreamPlans " +
           "WHERE t.id = :taskId")
    Optional<TaskEntity> findByIdWithAllRelations(@Param("taskId") String taskId);

    /**
     * Batch find tasks by IDs with files (optimized for bulk operations).
     */
    @Query("SELECT DISTINCT t FROM TaskEntity t " +
           "LEFT JOIN FETCH t.files " +
           "WHERE t.id IN :taskIds")
    List<TaskEntity> findByIdsWithFiles(@Param("taskIds") List<String> taskIds);

    /**
     * Find tasks by upstream plan with files loaded.
     */
    @Query("SELECT DISTINCT t FROM TaskEntity t " +
           "LEFT JOIN FETCH t.files " +
           "WHERE t.upstreamPlan.id = :planId")
    List<TaskEntity> findByUpstreamPlanIdWithFiles(@Param("planId") String planId);
}