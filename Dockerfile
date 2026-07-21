# Production Dockerfile for 24/7 Kalshi Crypto Streak Email Monitor
FROM python:3.11-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY .env.example .env

# Expose default environment
ENV POLL_INTERVAL_SECONDS=60
ENV RECIPIENT_EMAIL=danelujapare@gmail.com

# Entrypoint for 24/7 continuous real-time monitor
CMD ["python", "src/realtime_monitor.py"]
