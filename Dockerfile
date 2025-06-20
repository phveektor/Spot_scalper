FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot with environment variables
CMD ["python", "main.py", "run", "--mode", "${TRADING_MODE}", "--symbol", "${TRADING_SYMBOL}", "--timeframe", "${TRADING_TIMEFRAME}"] 