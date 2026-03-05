FROM python:3.9-slim

# Permette di rilevare l'architettura target durante buildx multi-platform
ARG TARGETARCH

# Dipendenze di build e runtime comuni
# Su Debian 13 (Trixie) alcune lib sono rinominate con suffisso t64 su tutte le arch
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    gcc \
    python3-dev \
    libffi-dev \
    libnss3 \
    libatk1.0-0t64 \
    libatk-bridge2.0-0t64 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2t64 \
    libxshmfence1 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Installa Chrome/Chromedriver in base all'architettura:
# - amd64: Google Chrome stable (build ufficiale Google)
# - arm64: chromium da apt (Google Chrome non ha build arm64 via .deb diretto)
# - altri: chromium da apt come fallback
RUN set -e; \
    if [ "$TARGETARCH" = "amd64" ]; then \
        wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
        && apt-get update \
        && apt-get install -y /tmp/chrome.deb \
        && rm /tmp/chrome.deb \
        && rm -rf /var/lib/apt/lists/* \
        && CHROME_VERSION=$(google-chrome --version | grep -oP '[0-9]+\.[0-9]+\.[0-9]+') \
        && DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}.0/linux64/chromedriver-linux64.zip" \
        && wget -q -O /tmp/chromedriver.zip "${DRIVER_URL}" \
        && unzip -o /tmp/chromedriver.zip -d /tmp/ \
        && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
        && chmod +x /usr/bin/chromedriver \
        && rm -rf /tmp/chromedriver* \
        && ln -sf /usr/bin/google-chrome /usr/bin/google-chrome-browser; \
    else \
        apt-get update \
        && apt-get install -y chromium \
        && (apt-get install -y chromium-driver || apt-get install -y chromium-chromedriver || true) \
        && rm -rf /var/lib/apt/lists/* \
        && ([ -f /usr/bin/chromium-browser ] && ln -sf /usr/bin/chromium-browser /usr/bin/google-chrome || ln -sf /usr/bin/chromium /usr/bin/google-chrome) \
        && ([ ! -f /usr/bin/chromedriver ] && [ -f /usr/lib/chromium/chromedriver ] && ln -sf /usr/lib/chromium/chromedriver /usr/bin/chromedriver || true); \
    fi

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

