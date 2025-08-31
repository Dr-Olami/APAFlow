# SMEFlow Development Setup

This guide will help you set up the SMEFlow development environment.

## Prerequisites

- Python 3.10+
- Docker Desktop
- Git

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd smeflow
   ```

2. **Run the setup script:**
   ```powershell
   # Windows PowerShell
   .\scripts\setup-dev.ps1
   ```

3. **Start the development server:**
   ```bash
   # Activate virtual environment
   .\.venv\Scripts\Activate.ps1  # Windows
   # source .venv/bin/activate    # Linux/Mac
   
   # Start the API server
   python -m smeflow.main
   ```

4. **Access the application:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Keycloak Admin: http://localhost:8080 (admin/admin)

## Manual Setup

### 1. Virtual Environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
pip install -e .
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Docker Services

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 4. Database Migration

```bash
alembic upgrade head
```

## Development Commands

### Running Tests

```bash
pytest
pytest --cov=smeflow  # With coverage
```

### Code Formatting

```bash
black smeflow/
isort smeflow/
```

### Type Checking

```bash
mypy smeflow/
```

### Database Operations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Project Structure

```
smeflow/
├── smeflow/           # Main application package
│   ├── core/          # Core configuration and utilities
│   ├── database/      # Database models and connection
│   ├── api/           # API routes and endpoints
│   └── main.py        # Application entry point
├── tests/             # Test files
├── alembic/           # Database migrations
├── scripts/           # Development scripts
├── config/            # Configuration files
└── docker-compose.dev.yml  # Development services
```

## Services

- **PostgreSQL**: Database (port 5432)
- **Redis**: Cache (port 6379)
- **Keycloak**: Authentication (port 8080)
- **LiveKit**: Voice communication (port 7880)
- **SMEFlow API**: Main application (port 8000)

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Reset database
docker-compose -f docker-compose.dev.yml down
docker volume rm smeflow_postgres_data
docker-compose -f docker-compose.dev.yml up -d postgres
```

### Port Conflicts

If you encounter port conflicts, update the ports in `docker-compose.dev.yml`.

### Permission Issues

On Windows, ensure Docker Desktop is running and you have proper permissions.

## Next Steps

After setting up the foundation:

1. **Phase 2**: Implement authentication with Keycloak
2. **Phase 3**: Create agent system with LangChain
3. **Phase 4**: Build workflow engine with LangGraph
4. **Phase 5**: Add integration layer with n8N
5. **Phase 6**: Implement voice communication with LiveKit
