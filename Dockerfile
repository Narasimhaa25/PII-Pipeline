FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for Presidio
RUN python -m spacy download en_core_web_lg

# Copy the entire project
COPY . .

# Default command (can be overridden in docker-compose)
CMD ["python", "consumer/pii_masker_presidio.py"]