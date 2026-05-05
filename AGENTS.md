# Repository Guidelines

## Project Structure & Module Organization
- Core application modules live in `app/` (`main_window.py`, `gesture_recognizer.py`, `state.py`, `view_3d.py`). Keep new GUI widgets or gesture logic in this package.
- `camera_handler.py` owns webcam capture and MediaPipe integration; `main.py` wires up the Tkinter boot sequence.
- Place gesture artwork in `icons/`; match file names to gesture enums (e.g., `open_hand.png`).
- Pytest suites sit in `tests/`; mirror module names (`tests/test_state.py`) when adding coverage.
- Store secrets in `.env` (e.g., `GEMINI_API_KEY`); never commit real keys.

## Build, Test, and Development Commands
- Create the virtual environment: `python -m venv .venv && .\.venv\Scripts\activate`.
- Install dependencies: `pip install -r requirements.txt`.
- Launch the app locally: `python main.py` (any `.env` overrides load automatically).
- Run unit tests: `python -m pytest`.
- Lint and format: `ruff check .`, `ruff format .`.
- Type-check and deep lint when touching core logic: `mypy app camera_handler.py` and `pylint app`.

## Coding Style & Naming Conventions
- Target Python 3.11 with strict typing; annotate new functions and public attributes.
- Follow Ruff defaults: 4-space indent, max line length 100, single quotes, sorted imports.
- Modules and functions use `snake_case`; classes `CamelCase`; constants `UPPER_SNAKE`.
- Keep GUI copy and gesture identifiers centralised in `app/config.py`.
- When adding assets, use lowercase filenames separated by underscores.

## Testing Guidelines
- Add new specs under `tests/` with filenames `test_<module>.py` and functions `test_<behavior>`.
- Use pytest fixtures for shared setup; keep assertions explicit.
- Run `python -m pytest --maxfail=1 --disable-warnings` before committing; document any skips.
- Extend scenario coverage for `AppState` transitions and MediaPipe integration boundaries.

## Commit & Pull Request Guidelines
- Follow the existing log style: `<type>: <imperative summary>` (example: `feat: Add open hand smoothing`).
- Group related changes per commit; explain why the change matters in the body for non-trivial updates.
- PRs should describe behaviour changes, reference issues, and attach screenshots or recordings of UI updates.
- Confirm lint, mypy, pytest, and manual app smoke-test results in the PR description.
- Flag configuration or asset changes so reviewers can reproduce locally.
