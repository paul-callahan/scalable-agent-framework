package com.pcallahan.agentic.graphbuilder.repository;

import com.pcallahan.agentic.graphbuilder.entity.AgentGraphEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository interface for AgentGraphEntity operations.
 */
@Repository
public interface AgentGraphRepository extends JpaRepository<AgentGraphEntity, String> {

    /**
     * Find all agent graphs for a specific tenant.
     */
    List<AgentGraphEntity> findByTenantIdOrderByCreatedAtDesc(String tenantId);

    /**
     * Find an agent graph by tenant ID and graph name.
     */
    Optional<AgentGraphEntity> findByTenantIdAndGraphName(String tenantId, String graphName);

    /**
     * Find the latest agent graph for a tenant and graph name.
     */
    Optional<AgentGraphEntity> findTopByTenantIdAndGraphNameOrderByCreatedAtDesc(String tenantId, String graphName);

    /**
     * Find agent graph by process ID.
     */
    Optional<AgentGraphEntity> findByProcessId(String processId);

    /**
     * Check if an agent graph exists for tenant and graph name.
     */
    boolean existsByTenantIdAndGraphName(String tenantId, String graphName);

    /**
     * Count agent graphs for a tenant.
     */
    long countByTenantId(String tenantId);
}