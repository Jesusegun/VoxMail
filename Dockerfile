# =============================================================================
# DOCKERFILE - Instructions to Build Your App Container
# =============================================================================
# Think of this as a recipe for creating your app's environment

# Start with Python 3.11 (pre-installed Python on Linux)
FROM python:3.11-slim

# Set working directory inside the container
# This is like doing "cd /app" - all commands run from here
WORKDIR /app

# Install system dependencies that some Python packages need
# (gcc, build tools for compiling C extensions)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first (Docker caches this layer)
# If requirements don't change, this step is skipped on rebuild = faster!
COPY requirements.txt .

# Install Python packages
# --no-cache-dir saves space by not saving downloaded files
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy language model for NLP (using pip for reliability)
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Now copy all your application code
COPY . .

# Create directories for data storage
# -p means "create parent directories if needed, don't error if exists"
RUN mkdir -p data credentials ai_data templates static

# Set permissions (make files readable/writable)
RUN chmod -R 755 /app

# Expose port 8080 (Flask will listen on this port)
# This tells Fly.io which port to route traffic to
EXPOSE 8080

# Make start script executable
RUN chmod +x start.sh

# Run the startup script when container starts
# This starts both Flask web app and scheduler
CMD ["./start.sh"]
