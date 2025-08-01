# Installation Guide

This guide will help you set up the Scalable Agent Framework on your local machine.

## Prerequisites

- **Python 3.13.5** (latest version)
- **Git** (for cloning the repository)
- **uv** (Python package manager) - [Installation instructions below](#installing-uv)

## Installing uv

The project uses `uv` as the Python package manager for faster dependency resolution and virtual environment management.

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation
```bash
uv --version
```

## Project Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd scalable-agent-framework
```

### 2. Activate uv (if needed)
If you just installed uv, you may need to add it to your PATH:
```bash
source scripts/activate_uv.sh
```

### 3. Install Dependencies
```bash
./setup.sh
```

This script will:
- Check if `uv` is installed
- Verify Python 3.13.5 is available
- Create/use the `.venv` directory
- Install all project dependencies using `uv sync`
- Verify installation with latest dependency versions

### 4. Activate the Virtual Environment
```bash
# Option 1: Run commands directly in the virtual environment
uv run python <script>

# Option 2: Activate the virtual environment for interactive use
source .venv/bin/activate
```

### 5. Generate Protobuf Files
The framework uses Protocol Buffers for communication. Generate the required Python files:
```bash
./scripts/gen_proto.sh
```

This script will:
- Generate `*_pb2.py` and `*_pb2_grpc.py` files from `.proto` definitions
- Fix import statements for proper package structure
- Verify all required files are generated

## Project Structure

After setup, your project structure should look like:

```
scalable-agent-framework/
├── protos/                         # Protocol Buffer definitions
│   ├── common.proto
│   ├── plan.proto
│   ├── services.proto
│   └── task.proto
├── services/standalone-py/
│   └── agentic/
│       ├── core/                   # Core framework classes
│       ├── control_plane/          # Control plane server
│       ├── data_plane/             # Data plane server
│       └── pb/                     # Generated protobuf files
├── scripts/
│   ├── activate_uv.sh             # uv activation helper
│   └── gen_proto.sh               # Protobuf generation script
├── setup.sh                       # Main setup script
├── pyproject.toml                 # Project configuration
└── uv.lock                       # Dependency lock file
```

## Development Workflow

### Running the Framework

1. **Run commands in the virtual environment:**
   ```bash
   # Start control plane server
   uv run python -m agentic.control_plane.server
   
   # Start data plane server (in another terminal)
   uv run python -m agentic.data_plane.server
   ```

   **Or activate the environment for interactive use:**
   ```bash
   source .venv/bin/activate
   
   # Then run your commands
   python -m agentic.control_plane.server
   ```

2. **Health Check Endpoints:**
   ```bash
   # Control plane health (HTTP)
   curl http://localhost:8080/health
   
   # Data plane health (HTTP)
   curl http://localhost:8081/health
   
   # Service metrics
   curl http://localhost:8080/metrics
   ```

3. **Demo Script:**
   ```bash
   # Run the logging and health check demo
   uv run python example_logging_demo.py
   ```

### Regenerating Protobuf Files

If you modify any `.proto` files, regenerate the Python bindings:
```bash
./scripts/gen_proto.sh
```

### Adding Dependencies

Add new dependencies using `uv`:
```bash
uv add package-name
```

For development dependencies:
```bash
uv add --dev package-name
```

### Running Commands

Run any command in the virtual environment:
```bash
uv run python <script>
uv run -m <module>
uv run pytest
uv run mypy .
```

## Dependency Management

### Latest Dependency Versions

The project uses the latest stable versions as of August 2025:

- **grpcio**: 1.74.0
- **grpcio-tools**: 1.74.0
- **protobuf**: 6.31.1
- **pydantic**: 2.7.3
- **aiohttp**: 3.9.5
- **structlog**: 24.1.0
- **asyncio-mqtt**: 0.16.2
- **aiofiles**: 24.1.0
- **click**: 8.1.7

### Development Dependencies

- **pytest**: 8.2.2
- **pytest-asyncio**: 0.24.0
- **pytest-cov**: 5.0.0
- **pytest-mock**: 3.14.0
- **black**: 24.7.0
- **isort**: 5.13.2
- **flake8**: 7.0.0
- **mypy**: 1.11.0
- **pre-commit**: 3.8.0

### Updating Dependencies

Update all dependencies to their latest versions:
```bash
make update-deps
```

Sync dependencies with the lock file:
```bash
make sync
```

## Troubleshooting

### Common Issues

1. **"uv command not found"**
   - Make sure uv is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Add to PATH: `source scripts/activate_uv.sh`

2. **Python version mismatch**
   - The project requires Python 3.13.5
   - Check your version: `uv run python --version`
   - Install Python 3.13.5 if needed

3. **Virtual environment issues**
   - Delete `uv.lock` and run `uv sync` to recreate the environment
   - Use `uv run` to run commands in the environment
   - Use `source .venv/bin/activate` to activate for interactive use

4. **Protobuf generation fails**
   - Ensure `grpcio-tools` is installed: `uv sync`
   - Check that `.proto` files are in the `protos/` directory
   - Verify the virtual environment exists: `ls -la .venv`

5. **Import errors in generated files**
   - Run `./scripts/gen_proto.sh` to regenerate and fix imports
   - Check that the `pb/` directory contains all required files

6. **Dependency conflicts**
   - Clear the virtual environment: `rm -rf .venv`
   - Reinstall: `uv sync`
   - Check for conflicting packages: `uv run pip list`

### Getting Help

- Check the [README.md](README.md) for project overview and architecture
- Review the [docs/](docs) directory for detailed documentation
- Examine the [protos/](protos) files to understand the data structures

## Next Steps

After installation, you can:

1. **Explore the codebase** - Start with `services/standalone-py/agentic/core/`
2. **Run examples** - Check for example scripts in the project
3. **Build your first agent** - Create custom Tasks and Plans
4. **Deploy to cloud** - Follow cloud deployment guides (when available)

## New Features

The framework now includes comprehensive structured logging and health checks:

- **Structured Logging**: JSON-formatted logs with request/response tracking and error handling
- **Health Checks**: HTTP endpoints for monitoring service health and readiness
- **Graceful Shutdown**: Proper cleanup and shutdown handling for both gRPC and HTTP servers
- **Metrics Collection**: Basic metrics tracking for monitoring and observability

See `services/standalone-py/LOGGING_AND_HEALTH.md` for detailed documentation.

## System Requirements

- **Python**: 3.13.5 (latest version)
- **Memory**: 2GB+ RAM recommended
- **Storage**: 1GB+ free space
- **Network**: Internet access for dependency installation

## Supported Platforms

- **macOS**: 10.15+ (Catalina)
- **Linux**: Ubuntu 18.04+, CentOS 7+, RHEL 7+
- **Windows**: Windows 10+ (with WSL2 recommended) 
