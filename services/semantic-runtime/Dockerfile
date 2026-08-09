FROM ghcr.io/astral-sh/uv:0.8.4 AS uv

FROM python:3.11.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/agent-runtime/pyproject.toml services/agent-runtime/pyproject.toml
COPY services/agent-runtime/src services/agent-runtime/src
COPY services/semantic-runtime services/semantic-runtime

RUN uv sync --frozen --no-dev --package tidewise-semantic-runtime

EXPOSE 8000 8100

CMD ["semantic-runtime"]
