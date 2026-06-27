FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PORT=8000

WORKDIR /app

# Minimal build tools for dependencies that need compilation + bash for entrypoint
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential bash && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend ./backend
WORKDIR /app/backend

# Create default data directories (can be overridden by env)
RUN mkdir -p data/uploads data/tmp
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["bash", "./entrypoint.sh"]

