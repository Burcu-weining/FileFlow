
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY api/ ./api/
COPY web/ ./web/
COPY start_server.sh .

RUN chmod +x start_server.sh

RUN useradd --create-home fileflow
USER fileflow

CMD ["./start_server.sh"]
