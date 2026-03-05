FROM python:3.9-slim

# Install dependencies for Chrome and C extensions
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    gcc \
    python3-dev \
    libffi-dev \
    # Dipendenze runtime per Chrome
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Installa Google Chrome stable (versione recente)
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# Installa chromedriver compatibile con la versione di Chrome installata
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '[0-9]+\.[0-9]+\.[0-9]+') \
    && DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}.0/linux64/chromedriver-linux64.zip" \
    && echo "Downloading chromedriver for Chrome ${CHROME_VERSION} from ${DRIVER_URL}" \
    && wget -q -O /tmp/chromedriver.zip "${DRIVER_URL}" \
    && unzip -o /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf /tmp/chromedriver*

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

