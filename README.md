# 🎥 Welding Detector

System wizyjny do monitorowania procesu spawania laserowego z kamerą USB.

## 📋 Opis

Welding Detector to aplikacja do podglądu i nagrywania procesu spawania w czasie rzeczywistym. 

**Główne funkcje:**
- 📹 Live streaming MJPEG z niskim opóźnieniem
- 🎬 Nagrywanie wideo do MP4 z prawidłową prędkością odtwarzania
- ⚙️ Ustawienia kamery (rozdzielczość HD/FHD, jakość JPEG)
- ⬛ Tryb monochromatyczny

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Camera Backend                                 │
│  MSMF (Media Foundation) → DirectShow → Auto (fallback chain)          │
│  Format: MJPG (hardware compressed) dla szybszego transferu USB         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CameraService (Unified)                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │ Background      │    │ Frame Buffer    │    │ MP4 Recording   │      │
│  │ Capture Thread  │───▶│ JPEG Encoding   │───▶│ + Re-encoding   │      │
│  │ (continuous)    │    │ (thread-safe)   │    │ (correct FPS)   │      │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐
            │ /camera/    │ │ /camera/    │ │ /recording/start    │
            │ stream      │ │ capture     │ │ /recording/stop     │
            │ (MJPEG)     │ │ (JPEG)      │ │ (MP4 recording)     │
            └─────────────┘ └─────────────┘ └─────────────────────┘
```

## 🔬 Mechanika działania

### 1. Inicjalizacja kamery

```python
# Próba uruchomienia z różnymi backendami (w kolejności)
backends = [
    MSMF,        # Media Foundation - najszybszy na Windows
    DirectShow,  # Klasyczny Windows API
    Auto         # Automatyczny wybór
]

# Optymalizacje
cap.set(CAP_PROP_BUFFERSIZE, 1)    # Minimalny bufor = mniejsze opóźnienie
cap.set(CAP_PROP_FOURCC, 'MJPG')   # Sprzętowa kompresja MJPEG
```

### 2. Pomiar rzeczywistego FPS

**Problem:** Kamera może nie wspierać żądanego FPS (np. żądamy 60, dostajemy 30).

**Rozwiązanie:** Mierzymy rzeczywisty FPS przez timing:
```python
def _measure_actual_fps():
    # Warmup - pierwsze klatki są niestabilne
    for _ in range(5):
        cap.read()
    
    # Pomiar: ile klatek w jakim czasie
    start = time.perf_counter()
    frames = 0
    for _ in range(60):
        if cap.read()[0]:
            frames += 1
    elapsed = time.perf_counter() - start
    
    actual_fps = frames / elapsed  # Np. 60 klatek / 2s = 30 FPS
```

### 3. Background Capture Thread

Osobny wątek przechwytuje klatki tak szybko jak kamera je dostarcza:

```python
def _capture_loop():
    while running:
        ret, frame = cap.read()  # Blokujące - czeka na klatkę
        
        # Opcjonalnie: konwersja do grayscale
        if monochrome:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Kodowanie do JPEG
        _, buf = cv2.imencode('.jpg', frame, [IMWRITE_JPEG_QUALITY, 95])
        
        # Thread-safe zapis do bufora
        with lock:
            last_frame = buf.tobytes()
            if recording:
                video_writer.write(frame)
```

### 4. Nagrywanie z prawidłowym FPS

**Problem:** Kamera deklaruje 60 FPS, ale realnie daje np. 17 FPS przez obciążenie systemu. 
Video nagrane z FPS=60 będzie odtwarzane 4x szybciej!

**Rozwiązanie:** Re-encoding z obliczonym FPS:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        RECORDING FLOW                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  START RECORDING                                                      │
│  ├─ Zapisz timestamp startu (perf_counter)                           │
│  ├─ Utwórz temp_*.mp4 z placeholder FPS (30)                         │
│  └─ Licz klatki (frame_count++)                                      │
│                                                                       │
│  STOP RECORDING                                                       │
│  ├─ Oblicz czas trwania: duration = now - start                      │
│  ├─ Oblicz realny FPS: real_fps = frame_count / duration             │
│  │   Przykład: 340 klatek / 19s = 17.9 FPS                           │
│  ├─ Re-encode temp_*.mp4 → final.mp4 z real_fps                      │
│  └─ Usuń temp file                                                   │
│                                                                       │
│  REZULTAT: Video 19s odtwarza się w 19s ✓                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 5. Streaming MJPEG

```python
async def stream_raw():
    while True:
        frame = get_frame()  # Pobierz ostatnią klatkę z bufora
        yield multipart_frame(frame)
        await sleep(1.0 / actual_fps)  # Throttle do realnego FPS
```

## 📂 Struktura projektu

```
welding-detector/
├── app/
│   ├── main.py                    # FastAPI app + lifespan
│   ├── api/
│   │   ├── routes.py              # Wszystkie endpointy
│   │   └── models.py              # Pydantic modele
│   ├── config/
│   │   └── settings.py            # Konfiguracja (.env)
│   └── services/
│       ├── camera_service.py      # Unified: capture + stream + record
│       ├── video_overlay_service.py    # Post-processing overlay
│       └── frame_overlay_service.py    # Live overlay (REC, timestamp)
├── app_frontend/
│   └── src/App.vue                # Vue 3 UI
├── recordings/                    # Zapisane nagrania MP4
├── .env                           # Konfiguracja
└── requirements.txt
```

## 🚀 Uruchomienie

### Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd app_frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up
```

## 📡 API Endpoints

### Camera
| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/camera/stream` | GET | MJPEG stream |
| `/camera/stream/overlay` | GET | Stream z live overlay (REC, timestamp) |
| `/camera/capture` | GET | Pojedyncza klatka JPEG |
| `/camera/health` | GET | Status kamery |
| `/camera/settings` | GET/PUT | Ustawienia (rozdzielczość, jakość JPEG) |
| `/camera/monochrome` | GET/POST | Tryb czarno-biały |

### Recording
| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/recording/start` | POST | Rozpocznij nagrywanie |
| `/recording/stop` | POST | Zatrzymaj + re-encode z prawidłowym FPS |
| `/recording/status` | GET | Status nagrywania (czas, klatki) |
| `/recording/list` | GET | Lista nagrań |
| `/recording/download/{filename}` | GET | Pobierz nagranie |
| `/recording/{filename}` | DELETE | Usuń nagranie |
| `/recording/{filename}/apply-overlay` | POST | Nałóż timestamp na istniejące video |

## ⚙️ Konfiguracja

Plik `.env`:
```env
CAMERA_INDEX=0              # Indeks kamery USB
CAMERA_USB_FPS=60           # Żądany FPS (rzeczywisty może być niższy)
CAMERA_USB_WIDTH=1280       # Szerokość (1280=HD, 1920=FHD)
CAMERA_USB_HEIGHT=720       # Wysokość (720=HD, 1080=FHD)
CAMERA_JPEG_QUALITY=95      # Jakość JPEG (1-100)
```

## 🔧 Technologie

| Technologia | Użycie |
|-------------|--------|
| **OpenCV** | Video capture (MSMF/DirectShow), JPEG encoding, VideoWriter |
| **FastAPI** | REST API + MJPEG streaming |
| **Vue 3** | Frontend SPA |
| **Tailwind CSS v4** | Stylowanie UI |
| **Pydantic** | Walidacja danych |

### Windows Camera Backends

| Backend | Opis | Wydajność |
|---------|------|-----------|
| **MSMF** | Media Foundation (Windows 7+) | ⭐⭐⭐ Najszybszy |
| **DirectShow** | Klasyczne Windows API | ⭐⭐ Dobry |
| **Auto** | Automatyczny wybór OpenCV | ⭐ Fallback |

Aplikacja automatycznie próbuje backendów w powyższej kolejności.

## 📝 Licencja

MIT
