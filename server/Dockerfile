# Backend Dockerfile using Python
FROM python:3.11-slim

WORKDIR /app

# Install uv for faster dependency installation (optional but recommended)
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY app ./app

# Create data directory for database and uploads
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
