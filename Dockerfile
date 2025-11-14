FROM python:3.10-slim

WORKDIR /app

# Copy entire project
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


ENV PYTHONPATH="/app"

CMD ["python", "consumer/pii_GPTmasker.py"]