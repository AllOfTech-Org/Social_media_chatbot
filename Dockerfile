# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependencies file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Run using Gunicorn in production mode
CMD ["gunicorn", "-b", "0.0.0.0:5000", "server:app"]
