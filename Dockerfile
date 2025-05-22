FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     libgl1-mesa-glx     libglib2.0-0     libsm6     libxext6     libxrender-dev     libgomp1     libglib2.0-0     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/hairstyles uploads

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
