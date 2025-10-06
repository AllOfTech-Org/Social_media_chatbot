# Use a Python base image, preferably one with miniconda for optimized environment
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (important for FAISS and other libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code and RAG data
COPY . .

# Set the environment variable for Gunicorn to bind to port 7860
ENV PORT 7860
EXPOSE 7860

# Command to run the application using Gunicorn (a production web server)
# The format is 'gunicorn [module_name]:[app_instance] -b 0.0.0.0:$PORT'
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 4 server:app