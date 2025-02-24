# Use an official lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port 5000 for the Flask app
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
