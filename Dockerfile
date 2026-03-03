FROM python:3.9-slim

# Install dependencies for Chromium, undetected-chromedriver and C extensions
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    gcc \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Crea le directory di persistenza
RUN mkdir -p /app/logs /app/data

# Run the bot
CMD ["python", "main.py"]

