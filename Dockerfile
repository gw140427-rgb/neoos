FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV NEOOS_DB=/data/database.db

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --chown=root:root Neoos.py ./
COPY --chown=root:root server.py ./
RUN chmod 0555 /app && chmod 0444 /app/Neoos.py /app/server.py \
    && useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin neoos \
    && mkdir -p /data \
    && chown 10001:10001 /data \
    && chmod 0700 /data

USER 10001:10001
EXPOSE 10000
CMD ["python3", "server.py"]
