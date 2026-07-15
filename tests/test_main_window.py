from collections.abc import Callable
from typing import Any

from app.main_window import MainWindow


class FakeRoot:
    def __init__(self) -> None:
        self.callbacks: dict[str, Callable[[], None]] = {}
        self.cancelled_jobs: list[str] = []

    def after(self, _delay: int, callback: Callable[[], None]) -> str:
        job = f'job-{len(self.callbacks) + 1}'
        self.callbacks[job] = callback
        return job

    def after_cancel(self, job: str) -> None:
        self.cancelled_jobs.append(job)


class FakeLabel:
    def __init__(self) -> None:
        self.options: dict[str, Any] = {}

    def config(self, **options: Any) -> None:
        self.options.update(options)


def test_action_status_returns_to_camera_ready_message() -> None:
    main_window = MainWindow.__new__(MainWindow)
    main_window.window = FakeRoot()  # type: ignore[assignment]
    main_window.status_bar = FakeLabel()  # type: ignore[assignment]
    main_window._status_message = ''
    main_window._status_from_action = False
    main_window._status_reset_job = None

    main_window._set_status('Kolor: Cyjan', is_action=True)
    main_window._clear_action_status()

    assert main_window._status_message == 'Kamera gotowa - wykonaj gest'
    assert main_window._status_from_action is False
    assert main_window._status_reset_job is None
    assert main_window.status_bar.options['text'] == 'Kamera gotowa - wykonaj gest'
