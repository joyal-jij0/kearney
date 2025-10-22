# Backend Dockerfile using Python with uv
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync
RUN uv sync --frozen --no-dev

# Copy application code
COPY app ./app

# Create data directory for database and uploads
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Run the application using uv run
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
