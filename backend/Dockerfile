#Build and test stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt /app/
RUN pip install -r requirements-dev.txt

COPY . .
# RUN pytest

#Development stage
FROM python:3.11-slim AS development

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt /app/
RUN pip install -r requirements-dev.txt

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

#Runtime stage (this is prod basically)
FROM python:3.11-slim AS production

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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]