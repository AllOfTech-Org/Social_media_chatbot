# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory to root of the repo
WORKDIR /workspace

# Copy dependency list first (better build caching)
COPY requirements.txt .

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# ✅ Set Hugging Face cache directories to writable paths
ENV HF_HOME=/workspace/hf_cache
ENV TRANSFORMERS_CACHE=/workspace/hf_cache
ENV SENTENCE_TRANSFORMERS_HOME=/workspace/hf_cache

# Create cache folder and make sure it's writable
RUN mkdir -p /workspace/hf_cache && chmod -R 777 /workspace/hf_cache

# Copy all source files (server.py, Chatbot.py, etc.)
COPY . .

# Expose port required by Hugging Face Spaces
EXPOSE 7860

# ✅ Run Flask app using Gunicorn (entrypoint for Spaces)
# "server:app" = file `server.py` with variable `app`
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "server:app"]
