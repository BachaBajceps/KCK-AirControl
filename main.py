"""
Punkt startowy aplikacji.
Tworzy główne okno i uruchamia pętlę zdarzeń.
"""

import tkinter as tk

from cube_app import CubeApp

if __name__ == "__main__":
    root = tk.Tk()
    app = CubeApp(root, "Sterowanie Obiektem 3D za pomocą Gestów")
    root.mainloop()
