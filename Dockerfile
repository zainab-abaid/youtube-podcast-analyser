# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv directly to /usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv ~/.cargo/bin/uv /usr/local/bin/ 2>/dev/null || mv ~/.local/bin/uv /usr/local/bin/ 2>/dev/null || true

# Verify uv installation
RUN uv --version

# Copy project files
COPY pyproject.toml uv.lock ./
COPY *.py ./
COPY .env* ./

# Create output directory
RUN mkdir -p output

# Install dependencies using uv
RUN uv sync --frozen

# Expose port
EXPOSE 12345

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:12345/api/tasks || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "12345"]
