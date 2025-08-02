package com.pcallahan.agentic.planexecutor.registry;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Registry for managing plan types and their handlers.
 * 
 * This registry:
 * - Maintains a mapping of plan types to their handler classes
 * - Provides methods to register and retrieve plan handlers
 * - Validates plan types and provides metadata
 */
@Component
public class PlanRegistry {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanRegistry.class);
    
    private final Map<String, Class<?>> planHandlers = new ConcurrentHashMap<>();
    private final Map<String, PlanMetadata> planMetadata = new ConcurrentHashMap<>();
    
    /**
     * Register a plan type with its handler class.
     * 
     * @param planType the plan type identifier
     * @param handlerClass the handler class
     * @param metadata metadata about the plan type
     */
    public void registerPlanType(String planType, Class<?> handlerClass, PlanMetadata metadata) {
        planHandlers.put(planType, handlerClass);
        planMetadata.put(planType, metadata);
        logger.info("Registered plan type: {} with handler: {}", planType, handlerClass.getName());
    }
    
    /**
     * Get the handler class for a plan type.
     * 
     * @param planType the plan type identifier
     * @return the handler class, or null if not found
     */
    public Class<?> getPlanHandler(String planType) {
        return planHandlers.get(planType);
    }
    
    /**
     * Check if a plan type is registered.
     * 
     * @param planType the plan type identifier
     * @return true if the plan type is registered
     */
    public boolean isPlanRegistered(String planType) {
        return planHandlers.containsKey(planType);
    }
    
    /**
     * Get all registered plan types.
     * 
     * @return array of registered plan types
     */
    public String[] getRegisteredPlanTypes() {
        return planHandlers.keySet().toArray(new String[0]);
    }
    
    /**
     * Get metadata for a plan type.
     * 
     * @param planType the plan type identifier
     * @return the plan metadata, or null if not found
     */
    public PlanMetadata getPlanMetadata(String planType) {
        return planMetadata.get(planType);
    }
    
    /**
     * Create a plan instance for the given plan type.
     * 
     * @param planType the plan type identifier
     * @return the plan instance, or null if creation failed
     */
    public Object createPlan(String planType) {
        try {
            Class<?> handlerClass = getPlanHandler(planType);
            if (handlerClass == null) {
                logger.error("No handler found for plan type: {}", planType);
                return null;
            }
            
            return handlerClass.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            logger.error("Failed to create plan instance for type: {}", planType, e);
            return null;
        }
    }
    
    /**
     * Metadata about a plan type.
     */
    public static class PlanMetadata {
        private final String description;
        private final String version;
        private final String author;
        
        public PlanMetadata(String description, String version, String author) {
            this.description = description;
            this.version = version;
            this.author = author;
        }
        
        public String getDescription() {
            return description;
        }
        
        public String getVersion() {
            return version;
        }
        
        public String getAuthor() {
            return author;
        }
    }
} 