'''
Punkt startowy aplikacji.
Tworzy główne okno, konfiguruje logowanie i uruchamia pętlę zdarzeń.
'''
import logging
import tkinter as tk
from cube_app import CubeApp

if __name__ == '__main__':
    # Konfiguracja logowania na samym początku
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
    )

    logging.info('Application starting...')
    root = tk.Tk()
    app = CubeApp(root, 'Sterowanie Obiektem 3D za pomocą Gestów')
    root.mainloop()
    logging.info('Application closed.')