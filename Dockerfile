FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ca-certificates && \
    pip install --no-cache-dir flask pymongo werkzeug
COPY . /app
CMD ["python", "app.py"]