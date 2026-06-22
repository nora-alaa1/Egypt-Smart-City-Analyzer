FROM python:3.11-slim

# lxml تحتاج libxml2 و libxslt على الـ slim image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY producer/ ./producer/
COPY consumer/ ./consumer/
COPY config/   ./config/

RUN mkdir -p output
