FROM python:3.11.7-slim

WORKDIR /app

COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./src .

ENTRYPOINT [ "python3", "-u", "client_mqtt.py" ]