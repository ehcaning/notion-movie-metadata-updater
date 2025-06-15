# syntax=docker/dockerfile:1
FROM python:3.13-alpine

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment variables (optional, for .env usage)
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "main.py"]
