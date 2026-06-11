ARG VERSION=3.12

FROM python:${VERSION}-bookworm

# uv: fast dependency installer/resolver (https://github.com/astral-sh/uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

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

# Verify Chrome and ChromeDriver installation
RUN echo "Chrome version:" && chromium --version && \
    echo "ChromeDriver version:" && chromedriver --version

COPY ./requirements.txt /code/requirements.txt

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r /code/requirements.txt

COPY . /code

EXPOSE 80

CMD ["fastapi", "run", "/code/main.py", "--proxy-headers",  "--port", "80", "--workers", "1"]
