FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/neoos

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 bash ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash neoos

WORKDIR /app
COPY bridge.py /app/bridge.py
RUN chown -R 1000:1000 /app /home/neoos

USER 1000:1000
EXPOSE 8081
CMD ["python3", "/app/bridge.py"]
