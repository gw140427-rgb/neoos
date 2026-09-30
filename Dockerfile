FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV NEOOS_DB=/data/database.db

RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin neoos
WORKDIR /app

COPY --chown=root:root Neoos.py server.py ./
RUN chmod 0555 /app && chmod 0444 /app/Neoos.py /app/server.py
RUN mkdir -p /data && chown 10001:10001 /data && chmod 0700 /data

USER 10001:10001
EXPOSE 10000
CMD ["python3", "server.py"]
