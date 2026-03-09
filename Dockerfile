# Use official Python image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Set a dummy SECRET_KEY so collectstatic can run
ENV SECRET_KEY="dummy-key-for-build-only"

# Run collectstatic
RUN python manage.py collectstatic --noinput

# Start gunicorn
CMD exec gunicorn portfolio_project.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0
