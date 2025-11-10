# syntax=docker/dockerfile:1

# Use official Python runtime as base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy script with inline dependencies (PEP 723)
COPY historical_backfill.py .

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run with uv (handles PEP 723 inline dependencies)
CMD ["uv", "run", "historical_backfill.py"]
