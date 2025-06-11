# main.py
import tkinter as tk
from cube_app import CubeApp

# --- Punkt startowy aplikacji ---
if __name__ == "__main__":
    # Utworzenie głównego okna Tkinter
    root = tk.Tk()
    
    # Stworzenie instancji naszej aplikacji
    app = CubeApp(root, "Sterowanie Kostką 3D za pomocą Gestów")
    
    # Uruchomienie głównej pętli zdarzeń Tkinter
    root.mainloop()