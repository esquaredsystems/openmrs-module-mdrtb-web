# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and clean up
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Memcached (optional if needed)
RUN apt-get update && apt-get install -y memcached

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy the rest of the project files
COPY . /app

# Change working directory to where manage.py is located
WORKDIR /app/mdrtb

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Start Memcached and Gunicorn using JSON format for CMD
CMD ["bash", "-c", "service memcached start && gunicorn --workers 2 --bind 0.0.0.0:8000 mdrtb.wsgi:application"]
