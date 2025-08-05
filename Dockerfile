FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py .
COPY fda_client.py .
COPY drug_processor.py .
COPY config.py .
COPY utils.py .
COPY manifest.json .

CMD ["python", "server.py"]