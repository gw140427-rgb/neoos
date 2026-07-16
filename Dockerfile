FROM ubuntu:24.04

RUN apt update && apt install -y \
    bash \
    curl \
    wget \
    python3

CMD ["bash"]
