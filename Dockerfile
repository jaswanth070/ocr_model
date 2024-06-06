# Stage 1: Build Stage
FROM python:3.9 AS builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV POPPLER_PATH=/usr/bin

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the Django project
COPY . .

# Stage 2: Production Stage
FROM python:3.9-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV POPPLER_PATH=/usr/bin

# Copy dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the Django project
COPY --from=builder /app /app

# Set working directory
WORKDIR /app

# Run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
