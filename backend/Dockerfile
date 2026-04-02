FROM python:3.12-slim

WORKDIR /code

# Install system dependencies for psycopg2 compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add the project root to PYTHONPATH so `from app.xxx` always resolves
ENV PYTHONPATH=/code
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run with a single worker by default; scale via --workers in production
# or use a process manager like Gunicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
