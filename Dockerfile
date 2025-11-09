# --- Dockerfile dla Backend API ---
FROM python:3.11-slim

# Metadata
LABEL maintainer="Welding Detector Team"
LABEL description="Backend API for Welding Detector - streams from camera-server"

# Ustaw katalog roboczy
WORKDIR /app

# Instaluj zależności systemowe (opcjonalnie, jeśli będziesz przetwarzać obrazy)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Skopiuj requirements i zainstaluj zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj kod aplikacji (tylko folder app, NIE camera_server)
COPY ./app ./app
COPY .env .

# Ustaw zmienną środowiskową
ENV PYTHONPATH=/app

# Port na którym działa aplikacja
EXPOSE 8000

# Uruchom Backend API (NIE camera_server!)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]