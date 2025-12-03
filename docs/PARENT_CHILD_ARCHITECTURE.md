# 🏗️ Parent-Child Architecture: Camera Services

## 📐 Architektura

```
Camera_USB_Service (parent)
    ↓ dziedziczy
RemoteCameraService (child)
```

---

## 🎯 Koncepcja

**RemoteCameraService** dziedziczy **wszystkie** cechy **Camera_USB_Service** i dodaje funkcjonalność proxy HTTP.

### ✅ Co daje dziedziczenie:

1. **Zero duplikacji kodu** - logika w jednym miejscu
2. **Spójny interfejs** - obie klasy mają te same metody
3. **Łatwa rozbudowa** - dodanie funkcji w parent automatycznie trafia do child
4. **Polymorphism** - można używać zamiennie gdzie oczekiwany jest Camera_USB_Service

---

## 📊 Porównanie Metod

### Metody DZIEDZICZONE (bez zmian)

| Metoda | Źródło | Opis |
|--------|--------|------|
| `start_recording()` | Parent | Włącza wskaźnik nagrywania |
| `stop_recording()` | Parent | Wyłącza wskaźnik nagrywania |

**Remote używa ich bez zmian** - działają na `self.is_recording`.

### Metody OVERRIDE (nadpisane w child)

| Metoda | Parent | Child (Remote) |
|--------|--------|----------------|
| `get_frame()` | Pobiera z USB (OpenCV) | Pobiera przez HTTP |
| `is_healthy()` | Sprawdza `cap.isOpened()` | Sprawdza HTTP health check |
| `get_stats()` | Stats USB kamery | Stats + remote server info |

**Remote override** - zachowuje interfejs, zmienia implementację.

### Metody DODATKOWE (tylko Remote)

| Metoda | Typ | Opis |
|--------|-----|------|
| `get_stream()` | async | MJPEG stream proxy |
| `health_check()` | async | Health check zdalnego serwera |
| `capture_frame_from_stream()` | async | Parsuje MJPEG → JPEG |
| `_fetch_frame_http()` | async | Helper do HTTP fetch |

**Remote tylko** - nie ma ich w parent, bo są specyficzne dla HTTP.

---

## 🧬 Atrybuty

### Wspólne (z parent)

```python
self.is_recording          # Recording state
self.last_frame            # Cached frame
self.consecutive_failures  # Error tracking
self.max_consecutive_failures
self.retry_delay
self.max_retries
```

### Specyficzne dla Remote

```python
self.camera_server_url     # URL do camera-server
self.stream_endpoint       # /stream endpoint
self.health_endpoint       # /health endpoint  
self.capture_endpoint      # /capture endpoint
```

### Różnice dla Remote

```python
self.camera_index = None   # Remote nie ma indexu
self.cap = None            # Remote nie ma VideoCapture
```

---

## 💻 Implementacja

### Parent: Camera_USB_Service

```python
class Camera_USB_Service:
    def __init__(self, camera_index=None):
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.is_recording = False
        # ... thread-safety, retry logic, etc.
    
    def get_frame(self) -> bytes:
        # Pobiera z USB kamery
        grabbed = self.cap.grab()
        success, frame = self.cap.retrieve()
        # ... overlay, encoding
        return jpeg_bytes
    
    def start_recording(self):
        self.is_recording = True
    
    def stop_recording(self):
        self.is_recording = False
```

### Child: RemoteCameraService

```python
class RemoteCameraService(Camera_USB_Service):
    def __init__(self):
        # NIE wywołuje super().__init__()
        # Kopiuje tylko potrzebne atrybuty
        self.is_recording = False
        self.last_frame = None
        # ... + remote-specific
        self.camera_server_url = settings.CAMERA_SERVER_URL
    
    def get_frame(self) -> bytes:
        # OVERRIDE: pobiera przez HTTP
        frame = asyncio.run(self._fetch_frame_http())
        return frame
    
    # start_recording(), stop_recording() - DZIEDZICZONE bez zmian
    
    async def get_stream(self):
        # DODATKOWA: tylko Remote ma
        async for chunk in response.aiter_bytes():
            yield chunk
```

---

## 🎯 Przykłady użycia

### 1. Używanie wspólnych metod

```python
from app.services.camera_USB_service import Camera_USB_Service
from app.services.remote_camera_service import RemoteCameraService

# Oba mają te same metody!
usb = Camera_USB_Service()
remote = RemoteCameraService()

# Recording control (dziedziczone)
usb.start_recording()      # ✅ działa
remote.start_recording()   # ✅ działa

usb.stop_recording()       # ✅ działa
remote.stop_recording()    # ✅ działa

# Get frame (różne implementacje)
frame_usb = usb.get_frame()     # Z USB przez OpenCV
frame_remote = remote.get_frame()  # Z HTTP przez httpx
```

### 2. Polymorphism

```python
def process_camera(camera: Camera_USB_Service):
    """Akceptuje USB lub Remote - oba działają!"""
    camera.start_recording()
    frame = camera.get_frame()
    stats = camera.get_stats()
    camera.stop_recording()
    return frame

# Oba działają
frame1 = process_camera(Camera_USB_Service())
frame2 = process_camera(RemoteCameraService())
```

### 3. Remote-specific features

```python
remote = RemoteCameraService()

# Metody z parent
remote.start_recording()  # ✅
frame = remote.get_frame()  # ✅ (overridden)

# Metody tylko Remote
import asyncio
stream = asyncio.run(remote.get_stream())  # ✅ tylko Remote ma
health = asyncio.run(remote.health_check())  # ✅ tylko Remote ma
```

---

## 🧪 Testowanie

```bash
# Test relationship
python test_parent_child.py
```

**Output:**
```
✅ start_recording()
✅ stop_recording()
✅ is_healthy()
✅ get_stats()
✅ get_frame()
🆕 get_stream()
🆕 health_check()
🆕 capture_frame_from_stream()
```

---

## 📈 Korzyści architektury

### ✅ Przed (duplikacja)

```python
# camera_USB_service.py
class Camera_USB_Service:
    def start_recording(self): ...
    def stop_recording(self): ...

# remote_camera_service.py  
class RemoteCameraService:
    def start_recording(self): ...  # ❌ DUPLIKACJA
    def stop_recording(self): ...   # ❌ DUPLIKACJA
```

**Problem:** 2x kod, 2x testy, 2x bugs

### ✅ Po (dziedziczenie)

```python
# camera_USB_service.py
class Camera_USB_Service:
    def start_recording(self): ...
    def stop_recording(self): ...

# remote_camera_service.py
class RemoteCameraService(Camera_USB_Service):
    # start_recording, stop_recording - DZIEDZICZONE ✅
    # tylko override co trzeba
```

**Korzyści:** 
- 1x kod
- 1x testy (parent)
- DRY principle
- Łatwa rozbudowa

---

## 🔧 Rozbudowa

### Dodanie nowej funkcji do parent

```python
# W Camera_USB_Service
class Camera_USB_Service:
    def get_fps(self) -> float:
        """Nowa metoda w parent."""
        return self.cap.get(cv2.CAP_PROP_FPS)
```

**Automatycznie dostępne w child:**
```python
remote = RemoteCameraService()
fps = remote.get_fps()  # ✅ działa od razu!
```

### Override w child jeśli potrzeba

```python
# W RemoteCameraService
class RemoteCameraService(Camera_USB_Service):
    def get_fps(self) -> float:
        """Override dla Remote - pobiera z HTTP."""
        stats = asyncio.run(self.health_check())
        return stats.get('fps', 0.0)
```

---

## 📝 Best Practices

### ✅ DO

1. **Dziedziczyć wspólną funkcjonalność** - start/stop recording
2. **Override co jest inne** - get_frame() inne dla USB vs HTTP
3. **Dodawać metody specyficzne** - get_stream() tylko w Remote
4. **Zachować interfejs** - override metody mają te same parametry
5. **Używać polymorphism** - funkcje akceptujące parent przyjmą child

### ❌ DON'T

1. **Nie duplikować kodu** - jeśli jest w parent, użyj dziedziczenia
2. **Nie łamać interfejsu** - override powinien zachować signature
3. **Nie mieszać odpowiedzialności** - USB = hardware, Remote = HTTP

---

## 🎓 Podsumowanie

```
Camera_USB_Service (parent)
├─ Cechy podstawowe: recording, caching, stats
├─ USB-specific: OpenCV, VideoCapture
└─ Interface: get_frame(), start_recording(), etc.

RemoteCameraService (child)
├─ DZIEDZICZY: recording, caching, stats ✅
├─ OVERRIDE: get_frame() (HTTP), is_healthy() (HTTP)
└─ DODAJE: get_stream(), health_check() (async HTTP)
```

**Rezultat:** Wspólny kod + specjalizacja = Optymalna architektura! 🎯
