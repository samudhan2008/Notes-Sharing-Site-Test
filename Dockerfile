FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y ca-certificates && \
    pip install --no-cache-dir flask pymongo

COPY . /app

CMD ["python", "app.py"]
