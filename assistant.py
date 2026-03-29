# This file exists at the project root so that `uv run python assistant.py`
# resolves `from src.xxx` imports correctly. Running src/app.py directly
# would fail with ModuleNotFoundError because the project root would not be
# on sys.path. Placing the entry point here ensures the root is always the
# working directory when the app starts.

from src.app import main

if __name__ == "__main__":
    main()
