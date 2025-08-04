package com.pcallahan.agentic.graphbuilder;

import com.pcallahan.agentic.graph.model.AgentGraph;
import com.pcallahan.agentic.graph.exception.GraphParsingException;
import com.pcallahan.agentic.graph.exception.GraphValidationException;
import com.pcallahan.agentic.graphbuilder.parser.GraphParser;
import com.pcallahan.agentic.graphbuilder.parser.GraphVizDotParser;
import com.pcallahan.agentic.graphbuilder.validation.PythonCodeBundleValidator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Facade service for building agent graphs from specifications.
 * 
 * <p>This service orchestrates the parsing and validation process for agent graph
 * specifications. It discovers available parsers, selects the appropriate parser
 * for a given specification file, and delegates the parsing and validation work.</p>
 * 
 * <p>The service supports multiple graph specification formats and can be easily
 * extended with new parsers by implementing the GraphParser interface.</p>
 */
@Service
public class GraphBuilderService {
    
    private static final Logger logger = LoggerFactory.getLogger(GraphBuilderService.class);
    
    private final List<GraphParser> parsers;
    
    /**
     * Creates a new GraphBuilderService with the default parsers.
     */
    public GraphBuilderService() {
        this.parsers = new ArrayList<>();
        this.parsers.add(new GraphVizDotParser());
        logger.info("Initialized GraphBuilderService with {} parsers", parsers.size());
    }
    
    /**
     * Creates a new GraphBuilderService with the specified parsers.
     * 
     * @param parsers The parsers to use
     */
    public GraphBuilderService(List<GraphParser> parsers) {
        this.parsers = new ArrayList<>(parsers);
        logger.info("Initialized GraphBuilderService with {} parsers", parsers.size());
    }
    
    /**
     * Builds an agent graph from a specification directory.
     * 
     * <p>This method:</p>
     * <ol>
     *   <li>Discovers the specification file in the directory</li>
     *   <li>Selects the appropriate parser for the file format</li>
     *   <li>Delegates parsing to the selected parser</li>
     *   <li>Returns the validated AgentGraph</li>
     * </ol>
     * 
     * @param specificationDirectory The directory containing the graph specification
     * @return A fully constructed and validated AgentGraph
     * @throws GraphParsingException if the specification cannot be parsed
     * @throws GraphValidationException if the graph violates integrity constraints
     * @throws IllegalArgumentException if the specification directory is invalid
     */
    public AgentGraph buildGraph(Path specificationDirectory) throws GraphParsingException, GraphValidationException {
        logger.info("Building agent graph from specification directory: {}", specificationDirectory);
        
        // Validate input
        if (specificationDirectory == null) {
            throw new IllegalArgumentException("Specification directory cannot be null");
        }
        
        if (!Files.exists(specificationDirectory)) {
            throw new IllegalArgumentException("Specification directory does not exist: " + specificationDirectory);
        }
        
        if (!Files.isDirectory(specificationDirectory)) {
            throw new IllegalArgumentException("Specification path is not a directory: " + specificationDirectory);
        }
        
        // Find the specification file
        Path specificationFile = findSpecificationFile(specificationDirectory);
        logger.debug("Found specification file: {}", specificationFile);
        
        // Find the appropriate parser
        GraphParser parser = findParser(specificationFile);
        if (parser == null) {
            throw GraphParsingException.parsingError(
                "No parser found for specification file: " + specificationFile.getFileName());
        }
        
        logger.info("Using parser: {} for file: {}", parser.getName(), specificationFile.getFileName());
        
        // Parse the graph
        try {
            AgentGraph graph = parser.parse(specificationDirectory);
            
            // Validate Python code bundles
            PythonCodeBundleValidator.validate(graph, specificationDirectory);
            
            logger.info("Successfully built agent graph with {} plans and {} tasks", 
                graph.planCount(), graph.taskCount());
            return graph;
        } catch (GraphParsingException e) {
            logger.error("Failed to parse graph specification: {}", e.getMessage());
            throw e;
        } catch (GraphValidationException e) {
            logger.error("Graph validation failed: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error building graph: {}", e.getMessage(), e);
            throw GraphParsingException.parsingError(
                "Unexpected error building graph: " + e.getMessage(), e);
        }
    }
    
    /**
     * Gets a list of supported file formats.
     * 
     * @return List of supported file extensions (e.g., [".dot", ".json"])
     */
    public List<String> getSupportedFormats() {
        return parsers.stream()
            .flatMap(parser -> Arrays.stream(parser.getSupportedExtensions()))
            .distinct()
            .collect(Collectors.toList());
    }
    
    /**
     * Gets information about available parsers.
     * 
     * @return List of parser information
     */
    public List<ParserInfo> getAvailableParsers() {
        return parsers.stream()
            .map(parser -> new ParserInfo(
                parser.getName(),
                Arrays.asList(parser.getSupportedExtensions())))
            .collect(Collectors.toList());
    }
    
    /**
     * Adds a new parser to the service.
     * 
     * @param parser The parser to add
     */
    public void addParser(GraphParser parser) {
        if (parser != null) {
            parsers.add(parser);
            logger.info("Added parser: {}", parser.getName());
        }
    }
    
    private Path findSpecificationFile(Path specificationDirectory) throws GraphParsingException {
        try {
            return Files.list(specificationDirectory)
                .filter(Files::isRegularFile)
                .filter(this::isSupportedFile)
                .findFirst()
                .orElseThrow(() -> GraphParsingException.parsingError(
                    "No supported specification file found in directory: " + specificationDirectory));
        } catch (Exception e) {
            throw GraphParsingException.parsingError(
                "Error searching for specification file in directory: " + specificationDirectory, e);
        }
    }
    
    private boolean isSupportedFile(Path file) {
        return parsers.stream().anyMatch(parser -> parser.supports(file));
    }
    
    private GraphParser findParser(Path specificationFile) {
        return parsers.stream()
            .filter(parser -> parser.supports(specificationFile))
            .findFirst()
            .orElse(null);
    }
    
    /**
     * Information about a graph parser.
     */
    public static class ParserInfo {
        private final String name;
        private final List<String> supportedExtensions;
        
        public ParserInfo(String name, List<String> supportedExtensions) {
            this.name = name;
            this.supportedExtensions = supportedExtensions;
        }
        
        public String getName() {
            return name;
        }
        
        public List<String> getSupportedExtensions() {
            return supportedExtensions;
        }
        
        @Override
        public String toString() {
            return "ParserInfo{" +
                "name='" + name + '\'' +
                ", supportedExtensions=" + supportedExtensions +
                '}';
        }
    }
} 