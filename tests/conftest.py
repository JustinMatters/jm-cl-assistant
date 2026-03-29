"""Pytest configuration: custom markers and shared fixtures."""

import subprocess
import time

import ollama
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring a live Ollama instance",
    )


@pytest.fixture(scope="session")
def ollama_server():
    """Ensure the Ollama server is running for the test session.

    Checks whether Ollama is already reachable. If not, starts
    ``ollama serve`` as a subprocess and waits up to 30 seconds for it
    to become ready. The subprocess is terminated at the end of the
    session only if it was started here (a pre-existing Ollama process
    is left untouched).

    Raises:
        RuntimeError: If Ollama fails to become reachable within 30 s.
    """
    proc = None
    try:
        ollama.list()
    except Exception:
        proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            try:
                ollama.list()
                break
            except Exception:
                time.sleep(1)
        else:
            proc.terminate()
            raise RuntimeError(
                "Ollama server did not become ready within 30 seconds."
            )

    yield

    if proc is not None:
        proc.terminate()
