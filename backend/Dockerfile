#Build and test stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY . .
RUN pytest

#Runtime stage (this is prod basically)
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Only copy production requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy only necessary files from builder
COPY --from=builder /app/main.py .
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic ./alembic

EXPOSE 8000
CMD CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]