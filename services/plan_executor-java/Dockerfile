# Runtime stage for Plan Executor Java microservice
# JAR file should be built outside Docker and copied to this image
FROM openjdk:21

# curl is already available in the base image

# Create non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy the pre-built JAR from host (built outside Docker)
COPY target/plan_executor-java-*.jar app.jar

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port for Spring Boot actuator
EXPOSE 8083

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8083/actuator/health || exit 1

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"] 