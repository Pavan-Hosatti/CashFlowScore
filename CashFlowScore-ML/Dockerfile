FROM python:3.11-slim

# System libs needed by numba/llvmlite and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Remove the local venv so it doesn't shadow installed packages
RUN rm -rf venv

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
