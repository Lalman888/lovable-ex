# 1. Base Image
FROM python:3.11-slim

# Set environment variables to prevent buffering of stdout/stderr and disable bytecode generation
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# 2. Install build dependencies (and potentially runtime ones if needed)
# Install gcc and other build essentials for potential C extensions during pip install
# Clean up afterwards to keep the image size down
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    # Add any other system dependencies required by your Python packages here
    # e.g., libpq-dev for psycopg2, etc.
    # If packages don't require C extensions, this whole RUN block might be removable
    # after verifying the pip install works without it.
    apt-get purge -y --auto-remove gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# 3. Set Working Directory
WORKDIR /app

# 4. Copy requirements file from the project root to the working directory
# Ensure the build context is the project root when running `docker build`
COPY requirements.txt .

# 5. Install Python dependencies
# --no-cache-dir: Disables the pip cache
# --compile: Compiles py files to pyc (optional, might speed up startup slightly)
RUN pip install --no-cache-dir --compile -r requirements.txt

# 6. Copy application code
# Copy the entire local 'app' directory into the '/app' directory in the image
# This assumes the Docker build context is the project root.
COPY ./app /app

# 7. Expose port for FastAPI application
EXPOSE 8000

# 8. Default command (will be overridden by docker-compose for worker/beat)
# Runs the FastAPI application using Uvicorn by default
# Use 0.0.0.0 to bind to all network interfaces within the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Note: docker-compose.yml should override this CMD for worker and beat services.
# Example for worker in docker-compose.yml:
# command: ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
# Example for beat in docker-compose.yml (using default scheduler):
# command: ["celery", "-A", "app.tasks", "beat", "--loglevel=info"]
