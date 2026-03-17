FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create log directories
RUN mkdir -p logs/failed_articles

# Expose FastAPI port
EXPOSE 8000

# Default: run FastAPI (scheduler runs as separate container)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
