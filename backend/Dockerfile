# Build and test stage
# python:3.11-slim
FROM python@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce AS builder

WORKDIR /app

RUN find /etc/apt -type f \( -name "*.list" -o -name "*.sources" \) \
    -exec sed -Ei \
      -e 's|^(URIs:[[:space:]]+)[^[:space:]]*deb\.debian\.org|\1https://deb.debian.org|g' \
      -e 's|^(URIs:[[:space:]]+)[^[:space:]]*security\.debian\.org|\1https://security.debian.org|g' \
      -e 's|^(deb[[:space:]]+)[^[:space:]]*deb\.debian\.org|\1https://deb.debian.org|g' \
      -e 's|^(deb[[:space:]]+)[^[:space:]]*security\.debian\.org|\1https://security.debian.org|g' \
      {} + \ 
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt /app/
RUN pip install -r requirements-dev.txt

COPY . .
# RUN pytest

# Development stage
# python:3.11-slim
FROM python@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce AS development

WORKDIR /app

RUN find /etc/apt -type f \( -name "*.list" -o -name "*.sources" \) \
    -exec sed -Ei \
      -e 's|^(URIs:[[:space:]]+)[^[:space:]]*deb\.debian\.org|\1https://deb.debian.org|g' \
      -e 's|^(URIs:[[:space:]]+)[^[:space:]]*security\.debian\.org|\1https://security.debian.org|g' \
      -e 's|^(deb[[:space:]]+)[^[:space:]]*deb\.debian\.org|\1https://deb.debian.org|g' \
      -e 's|^(deb[[:space:]]+)[^[:space:]]*security\.debian\.org|\1https://security.debian.org|g' \
      {} + \ 
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt /app/
RUN pip install -r requirements-dev.txt

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Runtime stage (this is prod basically)
# python:3.11-slim
FROM python@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce AS production

WORKDIR /app

RUN find /etc/apt -type f \( -name "*.list" -o -name "*.sources" \) \
    -exec sed -Ei \
      -e 's|^(URIs:[[:space:]]+)[^[:space:]]*deb\.debian\.org|\1https://deb.debian.org|g' \
      -e 's|^(URIs:[[:space:]]+)[^[:space:]]*security\.debian\.org|\1https://security.debian.org|g' \
      -e 's|^(deb[[:space:]]+)[^[:space:]]*deb\.debian\.org|\1https://deb.debian.org|g' \
      -e 's|^(deb[[:space:]]+)[^[:space:]]*security\.debian\.org|\1https://security.debian.org|g' \
      {} + \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system usergroup && adduser --system --no-create-home --ingroup usergroup appuser 

#second part of the above run is to create the suer

# Only copy production requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy only necessary files from builder
COPY --from=builder /app/main.py .
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/alembic.ini .
COPY --from=builder /app/seed.py .


RUN chown -R appuser:usergroup /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]