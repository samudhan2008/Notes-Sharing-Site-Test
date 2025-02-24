# Use the official Python image as a base
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the application files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app runs on
EXPOSE 5000

# Set the environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
