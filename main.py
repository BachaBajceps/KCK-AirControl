"""
Punkt startowy aplikacji.
Tworzy główne okno, konfiguruje logowanie i uruchamia pętlę zdarzeń.
"""
from __future__ import annotations

import argparse
import logging
import tkinter as tk

from app.main_window import MainWindow


def _run_application() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    logging.info('Application starting...')
    root = tk.Tk()
    MainWindow(root, 'Sterowanie Obiektem 3D za pomocą Gestów')
    root.mainloop()
    logging.info('Application closed.')


def main() -> None:
    parser = argparse.ArgumentParser(description='Sterowanie obiektem 3D gestami')
    parser.add_argument(
        '--calibrate',
        action='store_true',
        help='uruchamia interaktywną kalibrację zamiast aplikacji GUI',
    )
    args = parser.parse_args()

    if args.calibrate:
        from app.calibration import calibrate

        calibrate()
        return

    _run_application()


if __name__ == '__main__':
    main()
