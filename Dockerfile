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

# Default to HTTP transport in container
ENV TRANSPORT=http

# Smithery uses PORT; default 8081
ENV PORT=8081

CMD ["python", "server.py"]
