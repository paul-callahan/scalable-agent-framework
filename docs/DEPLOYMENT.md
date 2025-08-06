# Deployment Guide

This guide explains how to deploy the Scalable Agent Framework using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for containers
- At least 10GB disk space

## Quick Start

### 1. Build All Services

```bash
# Build all microservices
./scripts/build_microservices.sh

# Or build a specific service
./scripts/build_microservices.sh -s control-plane
```

### 2. Start Local Development Environment

```bash
# Start all services with Kafka and PostgreSQL
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.override.yml down
```

### 3. Access Services

- **Control Plane**: http://localhost:8001
- **Data Plane**: http://localhost:8002
- **Executor**: http://localhost:8003
- **Kafka UI**: http://localhost:8080
- **PostgreSQL**: localhost:5432

## Service Architecture

### Control Plane (Port 8001)
- **Purpose**: Request validation, policy enforcement, and routing
- **Health Check**: `GET /health/live`
- **API Documentation**: `GET /docs`

### Data Plane (Port 8002)
- **Purpose**: Data persistence and state management
- **Database**: PostgreSQL
- **Health Check**: `GET /health/live`
- **API Documentation**: `GET /docs`

### Executor (Port 8003)
- **Purpose**: Task and plan execution
- **Health Check**: `GET /health/live`
- **API Documentation**: `GET /docs`

### Infrastructure Services

#### Kafka (Port 9092)
- **Purpose**: Message broker for inter-service communication
- **Topics**: task-executions, plan-executions, persisted-task-executions,persisted-plan-executions, plan-inputs, task-inputs
- **Management**: Kafka UI at http://localhost:8080

#### PostgreSQL (Port 5432)
- **Purpose**: Persistent data storage for Data Plane
- **Database**: agentic
- **Credentials**: agentic/agentic

#### Zookeeper (Port 2181)
- **Purpose**: Kafka cluster coordination
- **Management**: Internal to Kafka

## Configuration

### Environment Variables

#### Common Variables
- `HOST`: Service host binding (default: 0.0.0.0)
- `PORT`: Service port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format (default: json)

#### Kafka Variables
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `KAFKA_CLIENT_ID`: Client identifier
- `KAFKA_GROUP_ID`: Consumer group identifier

#### Database Variables (Data Plane)
- `DATABASE_URL`: PostgreSQL connection string

### Configuration Files

#### Control Plane Policies
Location: `services/control-plane-py/policies/`
- `default.yaml`: Default execution policies
- Custom policies can be added and mounted

## Development Workflow

### 1. Local Development

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# View specific service logs
docker-compose logs -f control-plane

# Rebuild and restart a service
docker-compose build control-plane
docker-compose up -d control-plane
```

### 2. Testing

```bash
# Run tests for a specific service
cd services/control-plane-py
uv run pytest

# Run all tests
./scripts/build_microservices.sh -c  # Clean build
```

### 3. Debugging

```bash
# Access service container
docker-compose exec control-plane bash

# View service logs
docker-compose logs -f executor

# Check service health
curl http://localhost:8001/health/live
```

## Production Deployment

### 1. Environment-Specific Configuration

Create environment-specific override files:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  control-plane:
    environment:
      - LOG_LEVEL=WARNING
      - KAFKA_BOOTSTRAP_SERVERS=kafka-prod:9092
    restart: unless-stopped
```

### 2. Security Considerations

- Use secrets management for sensitive data
- Enable TLS for inter-service communication
- Configure proper network policies
- Use non-root users in containers

### 3. Monitoring

- Enable health checks for all services
- Configure log aggregation
- Set up metrics collection
- Implement alerting

### 4. Scaling

```bash
# Scale specific services
docker-compose up -d --scale executor=3

# Use external load balancer
docker-compose up -d --scale control-plane=2
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service logs
docker-compose logs service-name

# Check service health
curl http://localhost:8001/health/live

# Verify dependencies
docker-compose ps
```

#### 2. Kafka Connection Issues
```bash
# Check Kafka status
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check Kafka UI
open http://localhost:8080
```

#### 3. Database Connection Issues
```bash
# Check PostgreSQL
docker-compose exec postgres psql -U agentic -d agentic

# Check database migrations
docker-compose exec data-plane alembic current
```

### Log Analysis

```bash
# View all logs
docker-compose logs

# Filter logs by service
docker-compose logs control-plane | grep ERROR

# Follow logs in real-time
docker-compose logs -f --tail=100
```

## Performance Tuning

### Resource Limits

```yaml
# docker-compose.override.yml
services:
  control-plane:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### Kafka Optimization

- Adjust partition counts for topics
- Configure retention policies
- Tune producer/consumer settings
- Monitor consumer lag

### Database Optimization

- Configure connection pooling
- Optimize query performance
- Set up proper indexing
- Monitor slow queries

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U agentic agentic > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U agentic agentic < backup.sql
```

### Configuration Backup

```bash
# Backup configuration
tar -czf config-backup.tar.gz services/*/policies/ services/*/config/

# Restore configuration
tar -xzf config-backup.tar.gz
```

## Security Best Practices

1. **Network Security**
   - Use internal networks for service communication
   - Expose only necessary ports
   - Implement network policies

2. **Container Security**
   - Use non-root users
   - Scan images for vulnerabilities
   - Keep base images updated

3. **Data Security**
   - Encrypt data at rest and in transit
   - Use secrets management
   - Implement proper access controls

4. **Monitoring Security**
   - Monitor for suspicious activity
   - Implement audit logging
   - Regular security assessments 