ARG VERSION=3.12

FROM python:${VERSION}-bookworm

WORKDIR /code

# Install dependencies
RUN apt-get update && apt-get install -y

COPY ./requirements.txt /code/requirements.txt

RUN pip install playwright && \
    playwright install chromium

RUN pip install -r /code/requirements.txt

COPY . /code

EXPOSE 80

CMD ["fastapi", "run", "/code/main.py", "--proxy-headers",  "--port", "80", "--workers", "1"]
