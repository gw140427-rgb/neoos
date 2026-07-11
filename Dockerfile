FROM python:3.11-slim

WORKDIR /app
COPY Neoos.py /app/Neoos.py

CMD ["python", "Neoos.py"]
