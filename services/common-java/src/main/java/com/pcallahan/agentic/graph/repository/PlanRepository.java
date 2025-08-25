package com.pcallahan.agentic.graph.repository;

import com.pcallahan.agentic.graph.entity.PlanEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository interface for PlanEntity operations.
 */
@Repository
public interface PlanRepository extends JpaRepository<PlanEntity, String> {

    /**
     * Find all plans for a specific agent graph.
     */
    List<PlanEntity> findByAgentGraphId(String graphId);


    /**
     * Delete all plans for a specific agent graph.
     */
    void deleteByAgentGraphId(String graphId);
    
    /**
     * Find a plan by ID and agent graph ID.
     */
    Optional<PlanEntity> findByIdAndAgentGraphId(String id, String graphId);

    /**
     * Find all plans for a graph with files eagerly loaded (optimized query).
     */
    @Query("SELECT DISTINCT p FROM PlanEntity p " +
           "LEFT JOIN FETCH p.files " +
           "LEFT JOIN FETCH p.upstreamTasks " +
           "WHERE p.agentGraph.id = :graphId")
    List<PlanEntity> findByAgentGraphIdWithFiles(@Param("graphId") String graphId);

    /**
     * Find plan with all relationships for detailed view.
     */
    @Query("SELECT DISTINCT p FROM PlanEntity p " +
           "LEFT JOIN FETCH p.files " +
           "LEFT JOIN FETCH p.upstreamTasks " +
           "LEFT JOIN FETCH p.downstreamTasks " +
           "WHERE p.id = :planId")
    Optional<PlanEntity> findByIdWithAllRelations(@Param("planId") String planId);

    /**
     * Batch find plans by IDs with files (optimized for bulk operations).
     */
    @Query("SELECT DISTINCT p FROM PlanEntity p " +
           "LEFT JOIN FETCH p.files " +
           "WHERE p.id IN :planIds")
    List<PlanEntity> findByIdsWithFiles(@Param("planIds") List<String> planIds);
}