# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv directly to /usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv ~/.cargo/bin/uv /usr/local/bin/ 2>/dev/null || mv ~/.local/bin/uv /usr/local/bin/ 2>/dev/null || true

# Verify uv installation
RUN uv --version

# Copy frontend project files
COPY pyproject.toml ./
COPY *.py ./

# Install dependencies using uv
RUN uv sync

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit application
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
