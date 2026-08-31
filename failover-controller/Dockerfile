FROM python:3.12-slim

RUN find /etc/apt -type f \( -name "*.list" -o -name "*.sources" \) \
    -exec sed -Ei \
      -e 's|^(URIs:[[:space:]]+)([^[:space:]]*://)?(deb\.debian\.org)|\1https://\3|g' \
      -e 's|^(URIs:[[:space:]]+)([^[:space:]]*://)?(security\.debian\.org)|\1https://\3|g' \
      -e 's|^(deb[[:space:]]+)([^[:space:]]*://)?(deb\.debian\.org)|\1https://\3|g' \
      -e 's|^(deb[[:space:]]+)([^[:space:]]*://)?(security\.debian\.org)|\1https://\3|g' \
      {} + \
    && apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.lock .
RUN pip install \
    --no-cache-dir \
    --only-binary=:all: \
    --require-hashes \
    -r requirements.lock

COPY controller.py .

USER nobody

CMD ["python", "controller.py"]