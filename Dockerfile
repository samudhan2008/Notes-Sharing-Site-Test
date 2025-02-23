FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ca-certificates

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
