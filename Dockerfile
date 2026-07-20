FROM python:3.12-slim

WORKDIR /app

COPY ai_sdr_platform/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_sdr_platform /app/ai_sdr_platform

ENV PYTHONPATH=/app
ENV SDR_AUTH_ENABLED=true
ENV SDR_CORS_ORIGINS=http://localhost:8080

EXPOSE 8011

CMD ["uvicorn", "ai_sdr_platform.src.api.app:app", "--host", "0.0.0.0", "--port", "8011"]
