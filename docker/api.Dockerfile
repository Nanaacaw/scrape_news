FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/api.txt /app/requirements/api.txt
RUN pip install --no-cache-dir -r /app/requirements/api.txt

COPY . /app

RUN chmod +x /app/docker/entrypoint-api.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint-api.sh"]

