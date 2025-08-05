FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py .
COPY manifest.json .

# Copy utils directory with all utility modules
COPY utils/ ./utils/

# Copy documentation directory (optional but good to have)
COPY documentation/ ./documentation/

# Set environment variable for FDA API key (can be overridden at runtime)
ENV FDA_API_KEY=mpORfvSB8yDvTm1hD4Ud1snpNSsDwCY6u2W7qpdl

CMD ["python", "server.py"]