FROM python:3.12-slim

WORKDIR /app

COPY Neoos.py .
COPY server.py .

ENV PORT=10000
ENV NEOOS_DB=/app/database.db
EXPOSE 10000

CMD ["python3", "server.py"]
