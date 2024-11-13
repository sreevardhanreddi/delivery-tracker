ARG VERSION=3.12

FROM python:${VERSION}-slim-bullseye

WORKDIR /code

RUN apt-get update && apt-get install -y build-essential

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

COPY . /code

EXPOSE 80

CMD ["fastapi", "run", "/code/main.py", "--proxy-headers",  "--port", "80", "--workers", "1"]
