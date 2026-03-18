FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (Postgres-ready)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better caching)
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install .

# Copy full project
COPY . .

# Ensure instance folder exists
RUN mkdir -p instance

EXPOSE 5000

# Run app via Gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "wsgi:app"]