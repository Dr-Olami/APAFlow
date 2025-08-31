# SMEFlow Monolith MVP Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with uv
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 smeflow && chown -R smeflow:smeflow /app
USER smeflow

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "smeflow.main"]
