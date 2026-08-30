FROM python:3.12-slim

RUN find /etc/apt -type f \( -name "*.list" -o -name "*.sources" \) \
    -exec sed -i \
      -e 's|http://deb.debian.org|https://deb.debian.org|g' \
      -e 's|http://security.debian.org|https://security.debian.org|g' \
      {} + \
    && apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY controller.py .

USER nobody

CMD ["python", "controller.py"]