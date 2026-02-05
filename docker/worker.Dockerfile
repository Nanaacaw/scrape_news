FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/worker.txt /app/requirements/worker.txt
RUN pip install --no-cache-dir -r /app/requirements/worker.txt

COPY . /app

RUN chmod +x /app/docker/entrypoint-worker.sh

ENTRYPOINT ["/app/docker/entrypoint-worker.sh"]

