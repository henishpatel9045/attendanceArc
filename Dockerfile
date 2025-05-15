# Dockerfile

FROM python:3.12-slim AS builder
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 1. Install OS deps + build tools
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libgl1 libglib2.0-0 \
      build-essential python3-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 2. Install Python deps
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 3. Copy runtime packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 4. Copy app code & collect static
COPY . .
RUN python manage.py collectstatic --noinput

# 5. Expose port (for Compose + Nginx)
EXPOSE 8000
