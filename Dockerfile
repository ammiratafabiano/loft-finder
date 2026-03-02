FROM python:3.9-slim

# Install runtime capabilities and build dependencies in a single layer to save space.
# We use --no-install-recommends to avoid pulling unnecessary X11 desktop packages 
# for chromium. Then we install python packages and finally remove the C/C++ build tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    gcc \
    python3-dev \
    libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc python3-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "main.py"]

