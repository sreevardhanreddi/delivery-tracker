ARG VERSION=3.12

FROM python:${VERSION}-bookworm

WORKDIR /code

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--headless --no-sandbox --disable-dev-shm-usage --disable-gpu"
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV DISPLAY=:99

# Verify Chrome and ChromeDriver installation
RUN echo "Chrome version:" && chromium --version && \
    echo "ChromeDriver version:" && chromedriver --version

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

COPY . /code

# Create a script to start Xvfb and the application
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x16 &\nsleep 1\nexec "$@"' > /code/start.sh && \
    chmod +x /code/start.sh

EXPOSE 80

CMD ["/code/start.sh", "fastapi", "run", "/code/main.py", "--proxy-headers", "--port", "80", "--workers", "1"]
