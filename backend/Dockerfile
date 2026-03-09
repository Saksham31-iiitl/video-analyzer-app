FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install CLIP separately (requires git clone)
RUN pip install --no-cache-dir git+https://github.com/openai/CLIP.git

# Copy the rest of the backend code
COPY . .

# Create runtime directories
RUN mkdir -p uploads temp output cache music

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
