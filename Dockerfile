FROM ubuntu:latest

RUN apt update && apt install -y python3

CMD ["python3", "-m", "http.server", "10000"]