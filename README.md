# AirControl — sterowanie obiektem 3D gestami

Desktopowa aplikacja w Pythonie, która rozpoznaje gesty jednej dłoni z obrazu kamery i
steruje obiektem 3D renderowanym w interfejsie Tkinter. MediaPipe wykrywa punkty dłoni,
a klasyfikator oparty na kątach stawów rozpoznaje pięć gestów.

## Funkcje

- podgląd obrazu z kamery z naniesionymi punktami dłoni;
- stabilizacja rozpoznania na kilku kolejnych klatkach;
- obracanie sześcianu, piramidy lub kuli;
- zmiana koloru i kształtu, reset widoku oraz zatrzymanie obrotu;
- automatyczna próba odzyskania połączenia z kamerą;
- konfiguracja przez zmienne środowiskowe i plik `.env`;
- interaktywna kalibracja zapisująca wybrane ustawienia do `.env`.

## Sterowanie

| Gest | Działanie |
| --- | --- |
| Otwarta dłoń | Przesuwanie dłoni obraca obiekt wokół osi X i Y. |
| Palec wskazujący | Zmienia kolor na następny z palety. |
| Kciuk w górę | Zmienia kształt: sześcian → piramida → kula. |
| Victory | Przywraca domyślny widok. |
| Zaciśnięta pięść | Zatrzymuje obrót w bieżącej pozycji. |

Skróty klawiaturowe: `C` zmienia kolor, `S` zmienia kształt, a `R` resetuje widok.

## Wymagania

- Python 3.11 lub nowszy;
- kamera internetowa;
- systemowy Tkinter (jest dołączony do standardowej instalacji Pythona na Windowsie).

## Instalacja

W PowerShellu:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Uruchomienie aplikacji:

```powershell
python main.py
```

Uruchomienie interaktywnej kalibracji:

```powershell
python main.py --calibrate
```

Kalibracja porównuje dziesięć zestawów parametrów. Po zakończeniu najlepsze zaakceptowane
ustawienia są zapisywane do ignorowanego przez Git pliku `.env` i zostaną użyte przy
następnym uruchomieniu programu. Pozostałe wpisy w istniejącym `.env` są zachowywane.

## Konfiguracja

Wartości z prawdziwego środowiska mają pierwszeństwo przed `.env`. Obsługiwane klucze:

```dotenv
CAMERA_INDEX=0
CAMERA_MIN_DETECTION_CONFIDENCE=0.6
CAMERA_MIN_TRACKING_CONFIDENCE=0.5
CAMERA_FINGER_STRAIGHT_ANGLE_THRESHOLD=160
CAMERA_FINGER_BENT_ANGLE_THRESHOLD=100
CAMERA_THUMB_STRAIGHT_ANGLE_THRESHOLD=150
ANIMATION_SMOOTHING_FACTOR=0.08
ANIMATION_GESTURE_HISTORY_LENGTH=5
```

Niepoprawne wartości są zastępowane wartościami domyślnymi, a liczby spoza dozwolonego
zakresu są bezpiecznie ograniczane.

## Struktura projektu

```text
KCK-AirControl/
├── app/
│   ├── calibration.py       # interaktywny dobór parametrów
│   ├── config.py            # konfiguracja i obsługa .env
│   ├── gesture_recognizer.py
│   ├── main_window.py       # główne okno i pętla GUI
│   ├── state.py             # stan oraz stabilizacja gestów
│   ├── view_3d.py           # renderowanie figur
│   └── widgets.py           # współdzielone elementy GUI
├── icons/                   # ikony gestów
├── tests/                   # testy pytest
├── camera_handler.py        # OpenCV i MediaPipe
├── main.py                  # punkt wejścia CLI
├── requirements.txt         # zależności uruchomieniowe
└── requirements-dev.txt     # narzędzia deweloperskie
```

## Rozwój i weryfikacja

Zainstaluj narzędzia deweloperskie:

```powershell
python -m pip install -r requirements-dev.txt
```

Pełny zestaw lokalnych kontroli:

```powershell
python -m pytest --maxfail=1 --disable-warnings
python -m ruff check .
python -m ruff format --check .
python -m mypy app camera_handler.py main.py
python -m pylint app camera_handler.py main.py
```

Projekt nie zawiera kluczy ani innych sekretów. Lokalne pliki `.env` i środowiska `.venv`
są ignorowane przez Git.
