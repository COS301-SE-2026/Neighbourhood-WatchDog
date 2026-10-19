# Development stage
# python:3.11-slim
FROM python@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce AS development
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install -r requirements.txt

EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# Production stage
# python:3.11-slim
FROM python@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce AS production
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install -r requirements.txt \
    && addgroup --system usergroup && adduser --system --no-create-home --ingroup usergroup appuser

COPY app.py app_config.py authenticator.py bootstrap.py camera_runtime.py main.py watchdog_gui.py ./
COPY pipeline/ ./pipeline/
COPY runtime/ ./runtime/
COPY services/ ./services/
COPY ui/ ./ui/
# Add any other files that get created here explicitly

RUN chown -R appuser:usergroup /app
USER appuser

EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]