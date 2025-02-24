FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ca-certificates && \
    pip install --no-cache-dir flask pymongo werkzeug flask_pymongo

COPY . /app
COPY templates/ /app/templates/

CMD ["python", "app.py"]
