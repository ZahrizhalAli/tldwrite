# Use an official lightweight Python image
# 3.11 is stable and faster for newer AI libraries
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr (so logs show up immediately)
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# Your agent needs 'git' to clone repos and 'curl' for health checks
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caching optimization)
# If you change code but not requirements, Docker skips this step on rebuild
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# The command to run app
CMD ["streamlit", "run", "app.py"]