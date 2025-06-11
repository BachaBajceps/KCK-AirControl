
# Sterowanie Obiektem 3D za pomocą Gestów

Zaawansowana aplikacja w Pythonie demonstrująca sterowanie wirtualnym obiektem 3D w czasie rzeczywistym za pomocą gestów dłoni wykrywanych przez kamerę internetową. Projekt wykorzystuje zaawansowane techniki rozpoznawania obrazu i prezentuje interaktywny interfejs użytkownika.

*(W tym miejscu warto w przyszłości umieścić animowany GIF pokazujący działanie aplikacji)*


## Główne Funkcje

*   **Wyświetlanie obrazu na żywo** z kamery z nakładanymi punktami charakterystycznymi dłoni.
*   **Renderowanie obiektu 3D** (sześcian, piramida, kula) w dedykowanym panelu.
*   **Niezawodne wykrywanie gestów** dzięki logice opartej na analizie kątów między stawami, co zapewnia odporność na obrót dłoni i niską jakość kamery.
*   **Interaktywny interfejs użytkownika (GUI)** zbudowany w `Tkinter` z:
    *   Wizualnym panelem pokazującym wszystkie dostępne gesty i podświetlającym aktualnie aktywny.
    *   Podglądem obecnego i następnego koloru obiektu.
    *   Paskiem statusu informującym o bieżących akcjach.
*   **Pełne sterowanie obiektem za pomocą 5 różnych gestów.**

---

## Działanie i Obsługa

Po uruchomieniu aplikacji stań przed kamerą i używaj następujących gestów, aby kontrolować obiekt 3D:

| Gest | Ikona | Akcja |
| :--- | :---: | :--- |
| **Otwarta dłoń** | ✋ | **Obrót obiektu.** Przesuwaj dłoń po ekranie, aby płynnie obracać kształtem. Ruch lewo-prawo obraca wokół osi Y, a góra-dół wokół osi X. |
| **Palec wskazujący** | ☝️ | **Zmiana koloru.** Każde pokazanie tego gestu zmienia kolor obiektu na następny z predefiniowanej palety. |
| **Kciuk w górę** | 👍 | **Zmiana kształtu.** Zmienia renderowany obiekt cyklicznie (Sześcian → Piramida → Kula → Sześcian...). |
| **Zwycięstwo (Victory)**| ✌️ | **Resetowanie widoku.** Przywraca pozycję i orientację obiektu do domyślnej. |
| **Zaciśnięta pięść** | ✊ | **Zatrzymanie obrotu.** Gdy dłoń jest zaciśnięta, obiekt przestaje podążać za ruchem i pozostaje w ostatniej pozycji. |

---

## Technologie i Narzędzia

### Główne Technologie
*   **Python 3.11+**
*   **Tkinter:** Standardowa biblioteka GUI do tworzenia interfejsu.
*   **OpenCV-Python (`cv2`):** Do przechwytywania i przetwarzania obrazu z kamery.
*   **MediaPipe:** Biblioteka Google do precyzyjnego wykrywania dłoni i ich punktów charakterystycznych.
*   **Matplotlib:** Do renderowania i osadzania sceny 3D w oknie Tkinter.
*   **NumPy:** Do operacji matematycznych i wektorowych.
*   **Pillow (`PIL`):** Do konwersji formatów obrazu między OpenCV a Tkinter.

### Narzędzia Deweloperskie
*   **Mypy:** Do statycznej analizy typów, zapewniającej bezpieczeństwo i poprawność kodu.
*   **Ruff:** Ultraszybki linter i formatter do utrzymania wysokiej jakości i spójności kodu.
*   **Pylint:** Dodatkowe, głębokie analizy w poszukiwaniu potencjalnych błędów i "code smells".

---

## Struktura Projektu

```
KCK-AirControl/
├── icons/                # Folder z ikonami gestów (np. open_hand.png)
├── main.py               # Punkt startowy aplikacji, inicjuje główne okno.
├── cube_app.py           # Główna klasa aplikacji, zarządza UI i pętlą zdarzeń.
├── camera_handler.py     # Moduł odpowiedzialny za obsługę kamery i logikę rozpoznawania gestów.
├── pyproject.toml        # Plik konfiguracyjny dla Mypy, Ruff i Pylint.
└── requirements.txt      # Lista zależności projektu.
```

---

## Instalacja i Uruchomienie

1.  **Sklonuj repozytorium** lub pobierz pliki projektu.

2.  **Utwórz folder `icons`** w głównym katalogu projektu i umieść w nim pliki `.png` dla każdego gestu.

3.  **Utwórz i aktywuj wirtualne środowisko** (zalecane):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

4.  **Utwórz plik `requirements.txt`** i wklej do niego poniższą zawartość:
    ```txt
    opencv-python
    mediapipe
    matplotlib
    numpy
    Pillow
    ```

5.  **Zainstaluj wymagane biblioteki**:
    ```bash
    pip install -r requirements.txt
    ```

6.  **Uruchom aplikację**:
    ```bash
    python main.py
    ```
    Aplikacja powinna się uruchomić. Przy pierwszym uruchomieniu system może poprosić o dostęp do kamery.

---

## Dalszy Rozwój

Projekt można rozwijać w wielu kierunkach:

*   **Zmiana silnika 3D:** Zastąpienie `Matplotlib` wydajniejszą biblioteką do grafiki 3D, taką jak `PyOpenGL` lub `PyVista`, aby uzyskać płynniejszy rendering.
*   **Panel Konfiguracji:** Dodanie interfejsu, w którym użytkownik może dostosować czułość obrotu, przypisanie gestów do akcji czy paletę kolorów.
*   **Więcej Kształtów i Modeli:** Możliwość ładowania prostych modeli 3D z plików (np. `.obj`).
*   **Obsługa Dwóch Dłoni:** Rozszerzenie logiki do sterowania za pomocą obu dłoni (np. jedna do obrotu, druga do skalowania).
*   **Spakowanie do Pliku Wykonywalnego:** Użycie narzędzi takich jak `PyInstaller` do stworzenia samodzielnej aplikacji (`.exe`), która nie wymaga instalacji Pythona.