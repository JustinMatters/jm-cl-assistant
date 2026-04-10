FROM python:3.13-slim

# Install UV from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# curl is needed for the Ollama health-check in compose.yml.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies before copying source so this layer is cached
# when only source files change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy application source.
COPY . .

# Install the project itself (editable).
RUN uv sync --frozen

# Gradio must bind to all interfaces to be reachable outside the container.
ENV GRADIO_SERVER_NAME=0.0.0.0

EXPOSE 7860

# TTS (Kokoro) and STT (Whisper) require model files and system audio
# that are unavailable in a typical container environment.  Pass
# --no-tts / --no-stt to run in text-only mode.  Override CMD in
# compose.yml or at `docker run` time if you supply the model files.
CMD ["uv", "run", "python", "assistant.py", "--no-tts", "--no-stt"]
