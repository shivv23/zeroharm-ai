FROM python:3.11-slim
RUN adduser --disabled-password --no-create-home appuser && apt-get update && apt-get install -y --no-install-recommends wget && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
