# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Clone your repository at build time
RUN git clone https://github.com/esquaredsystems/openmrs-module-mdrtb-web
WORKDIR /app

# Copy settings file
COPY ./mdrtb/mdrtb/settings.py /app/mdrtb/mdrtb/

# Expose port 8000
EXPOSE 8000

# Ensure static files path is correctly set
ENV DJANGO_SETTINGS_MODULE=mdrtb.mdrtb.settings

# Collect static files
RUN python manage.py collectstatic --noinput --settings=mdrtb.mdrtb.settings

# Start Gunicorn
CMD ["gunicorn", "--workers", "8", "--bind", "0.0.0.0:8000", "mdrtb.wsgi:application"]
