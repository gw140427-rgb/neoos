FROM ubuntu:24.04

RUN apt update && apt install -y python3

WORKDIR /app

COPY server.py .

CMD ["python3", "server.py"]
