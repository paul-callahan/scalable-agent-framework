package com.pcallahan.agentic.graphbuilder.repository;

import com.pcallahan.agentic.graphbuilder.entity.PlanEntity;
import org.springframework.data.jpa.repository.JpaRepository;
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
     * Find a plan by graph ID and plan name.
     */
    Optional<PlanEntity> findByAgentGraphIdAndPlanName(String graphId, String planName);

    /**
     * Delete all plans for a specific agent graph.
     */
    void deleteByAgentGraphId(String graphId);
}