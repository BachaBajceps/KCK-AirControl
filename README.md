# Sterowanie Kostką 3D za pomocą Gestów

Prosta aplikacja w Pythonie demonstrująca sterowanie wirtualną kostką 3D w czasie rzeczywistym za pomocą gestów dłoni wykrywanych przez kamerę internetową.


*(W tym miejscu warto w przyszłości umieścić animowany GIF pokazujący działanie aplikacji)*

## Główne Funkcje

*   **Wyświetlanie obrazu na żywo** z kamery internetowej.
*   **Renderowanie obracanej kostki 3D** w tym samym oknie.
*   **Wykrywanie dłoni i gestów** za pomocą biblioteki MediaPipe.
*   **Sterowanie kostką:**
    *   Obrót kostki poprzez przesuwanie otwartej dłoni.
    *   Zmiana koloru kostki za pomocą gestu wskazywania palcem.

---

## Technologie

*   **Python 3:** Język programowania.
*   **Tkinter:** Standardowa biblioteka GUI do tworzenia interfejsu okna.
*   **OpenCV-Python (`cv2`):** Do przechwytywania obrazu z kamery.
*   **Matplotlib:** Do renderowania i osadzania sceny 3D (kostki) w oknie Tkinter.
*   **MediaPipe:** Zaawansowana biblioteka od Google do wykrywania dłoni i ich punktów charakterystycznych (landmarków).
*   **Pillow (`PIL`):** Do konwersji formatów obrazu między OpenCV a Tkinter.

---

## Struktura Plików

Projekt jest podzielony na logiczne moduły, aby ułatwić zarządzanie kodem:

```
projekt_kostka_3d/
├── main.py             # Punkt startowy aplikacji, inicjuje główne okno.
├── cube_app.py         # Główna klasa aplikacji, zarządza UI i stanem programu.
├── camera_handler.py   # Moduł odpowiedzialny za obsługę kamery i rozpoznawanie gestów.
└── requirements.txt    # Lista zależności projektu.
```

---

## Instalacja i Uruchomienie

1.  **Sklonuj repozytorium** (lub pobierz pliki i umieść je w jednym folderze).

2.  **Utwórz i aktywuj wirtualne środowisko** (zalecane):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Zainstaluj wymagane biblioteki** za pomocą pliku `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Uruchom aplikację**:
    ```bash
    python main.py
    ```
    Aplikacja powinna uruchomić się i poprosić o dostęp do kamery.

---

## Jak Używać?

Po uruchomieniu aplikacji stań przed kamerą i używaj następujących gestów:

*   ✋ **Otwarta dłoń**: Przesuwaj dłoń po ekranie, aby obracać kostką.
    *   Ruch **lewo-prawo** obraca kostkę wokół jej osi Y.
    *   Ruch **góra-dół** obraca kostkę wokół jej osi X.

*   ☝️ **Palec wskazujący**: Pokaż gest wskazywania, aby zmienić kolor kostki na następny z predefiniowanej listy. Aby akcja zadziałała ponownie, musisz na chwilę zmienić gest (np. na otwartą dłoń).

*   ✊ **Pięść / Brak dłoni**: Gdy dłoń jest zaciśnięta w pięść lub niewidoczna, kostka przestaje reagować na ruch i pozostaje w ostatniej pozycji.