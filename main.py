"""Command-line entry point for the AirControl GUI and calibration tool."""

from __future__ import annotations

import argparse
import logging
import tkinter as tk
from importlib import import_module
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.main_window import MainWindow


def _run_application() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%H:%M:%S',
    )

    logging.info('Application starting...')
    root = tk.Tk()
    main_window_type = cast(
        'type[MainWindow]',
        import_module('app.main_window').MainWindow,
    )
    main_window_type(root, 'Sterowanie Obiektem 3D za pomocą Gestów')
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
        calibrate = cast(
            'Callable[[], None]',
            import_module('app.calibration').calibrate,
        )
        calibrate()
        return

    _run_application()


if __name__ == '__main__':
    main()
