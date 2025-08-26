#!/bin/bash

# Build script for Java microservices
# This script builds all JAR files outside Docker, then builds Docker images

set -e

echo "Building Java microservices..."

# Build all JAR files first
echo "Building JAR files..."
mvn clean package -DskipTests

# Verify JAR files were created
echo "Verifying JAR files..."
for service in data-plane control-plane admin-java graph-builder graoh_composer; do
    jar_file="services/${service}/target/${service}-1.0.0.jar"
    if [ ! -f "$jar_file" ]; then
        echo "ERROR: JAR file not found: $jar_file"
        exit 1
    fi
    echo "✓ Found: $jar_file"
done

echo "All JAR files built successfully!"

# Build Docker images
echo "Building Docker images..."
for service in data-plane control-plane; do
    echo "Building Docker image for $service..."
    docker build -t agentic-$service:latest services/$service/
done

echo "All Docker images built successfully!" 