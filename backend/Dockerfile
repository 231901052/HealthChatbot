# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# install build deps needed for some Python packages (psycopg2 etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev gcc curl && apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy the backend code
COPY . /app

# ensure Python can import the 'app' package at runtime
ENV PYTHONPATH=/app

# default command to start uvicorn
CMD ["uvicorn", "app.main:app", "--host",  "0.0.0.0", "--port", "8000", "--reload"]
