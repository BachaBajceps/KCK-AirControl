# KCK AirControl

Projekt demonstracyjny pozwalający sterować wirtualnym obiektem 3D na podstawie ruchu dłoni odczytanego z kamery.  
Aplikacja wykorzystuje bibliotekę MediaPipe do wykrywania dłoni, a współrzędne przekazywane są do aplikacji webowej lub modułu 3D.

## Wymagania
* Python 3.11+
* Flask i Flask-CORS
* OpenCV (`opencv-python`)
* MediaPipe
* Pygame (do modułu OpenGL)
* Pillow (dla aplikacji Tkinter)

## Instalacja
1. Utwórz i aktywuj wirtualne środowisko (opcjonalnie).
2. Zainstaluj wymagane biblioteki:
   ```bash
   pip install flask flask-cors opencv-python mediapipe pygame pillow
   ```

## Uruchamianie
- **Serwer Flask**: 
  ```bash
  python app.py
  ```
  Po uruchomieniu wejdź na `http://localhost:53102` aby wyświetlić stronę.
- **GUI (Tkinter)**: 
  ```bash
  python gui_app.py
  ```
- **Demo kostki w OpenGL**:
  ```bash
  python cube_app.py
  ```

Uwaga: środowisko bez pełnej obsługi GUI lub akceleracji 3D może nie umożliwiać poprawnego działania części wizualnej.

## Testy
Testy jednostkowe znajdują się w pliku `test_hand_tracking.py` i można je uruchomić poleceniem:
```bash
pytest -q
```

## Struktura
- `app.py` – prosty serwer Flask przekazujący współrzędne dłoni.
- `gui_app.py` – aplikacja okienkowa z podglądem z kamery i miejscem na moduł 3D.
- `cube_app.py` – przykład renderowania kostki sterowanej ruchem dłoni (OpenGL + Pygame).
- `hand_tracking.py` – funkcje do przetwarzania pojedynczej klatki obrazu.
- `templates/index.html` – szablon strony z podglądem i placeholderem kostki 3D.

## Licencja
Kod jest udostępniony na licencji GNU GPLv3 – szczegóły w pliku `LICENSE`.
