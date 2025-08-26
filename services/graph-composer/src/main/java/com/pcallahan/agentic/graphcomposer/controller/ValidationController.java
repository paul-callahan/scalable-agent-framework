package com.pcallahan.agentic.graphcomposer.controller;

import com.pcallahan.agentic.graphcomposer.dto.AgentGraphDto;
import com.pcallahan.agentic.graphcomposer.dto.NodeNameValidationRequest;
import com.pcallahan.agentic.graphcomposer.dto.ValidationResult;
import com.pcallahan.agentic.graphcomposer.service.ValidationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;

/**
 * REST Controller for validation operations.
 * Provides endpoints for real-time graph and node validation.
 */
@RestController
@RequestMapping("/api/v1/validation")
@CrossOrigin(origins = "*", maxAge = 3600)
public class ValidationController {

    private final ValidationService validationService;

    public ValidationController(ValidationService validationService) {
        this.validationService = validationService;
    }

    /**
     * Validate a complete graph structure.
     *
     * @param graph the graph to validate
     * @return validation result with any errors or warnings
     */
    @PostMapping("/graph")
    public ResponseEntity<ValidationResult> validateGraph(@Valid @RequestBody AgentGraphDto graph) {
        ValidationResult result = validationService.validateGraph(graph);
        return ResponseEntity.ok(result);
    }

    /**
     * Validate a node name for uniqueness and format.
     *
     * @param request the node name validation request
     * @return validation result
     */
    @PostMapping("/node-name")
    public ResponseEntity<ValidationResult> validateNodeName(@Valid @RequestBody NodeNameValidationRequest request) {
        ValidationResult result = validationService.validateNodeName(request);
        return ResponseEntity.ok(result);
    }
}