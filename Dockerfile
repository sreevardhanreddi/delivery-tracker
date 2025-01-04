ARG VERSION=3.12

FROM python:${VERSION}-slim-bullseye

WORKDIR /code

# Install dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  wget \
  curl \
  unzip \
  fonts-liberation \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libatspi2.0-0 \
  libcups2 \
  libdbus-1-3 \
  libdrm2 \
  libgbm1 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libx11-xcb1 \
  libxcb-dri3-0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  xdg-utils \
  --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates

ARG CHROME_VERSION=131.0.6778.204

# Install Chrome for Testing
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" \
  && unzip chrome-linux64.zip \
  && mv chrome-linux64 /opt/chrome \
  && rm chrome-linux64.zip

# Install ChromeDriver
RUN CHROMEDRIVER_DIR="/usr/local/bin" \
  && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
  && unzip chromedriver-linux64.zip \
  && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
  && chmod +x /usr/local/bin/chromedriver \
  && rm -rf chromedriver-linux64.zip chromedriver-linux64

# Set environment variables for Chrome and ChromeDriver
ENV CHROME_BIN=/opt/chrome/chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

COPY . /code

EXPOSE 80

CMD ["fastapi", "run", "/code/main.py", "--proxy-headers",  "--port", "80", "--workers", "1"]
