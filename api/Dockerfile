# lean-data-kit/api/Dockerfile
# Use official slim Python runtime as parent image
FROM python:3.11-slim

# Prevent python from writing pyc files to disk and enable instant stdout logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define application working directory
WORKDIR /app

# Install system-level build tools for compiling performance dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to maximize Docker layer caching efficiency
COPY requirements.txt .

# Install Python package dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application codebase
COPY . .

# Create directory to store persistent DuckDB file inside container
RUN mkdir -p /app/data

# Expose FastAPI default port
EXPOSE 8000

# Command to execute the FastAPI server using Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
