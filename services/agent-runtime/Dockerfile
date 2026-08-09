FROM ghcr.io/astral-sh/uv:0.8.4 AS uv

FROM python:3.11.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=uv /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/agent-runtime services/agent-runtime
COPY services/semantic-runtime/pyproject.toml services/semantic-runtime/pyproject.toml
COPY services/semantic-runtime/src services/semantic-runtime/src

RUN uv sync --frozen --no-dev --package tidewise-agent-runtime

EXPOSE 8200

CMD ["agent-runtime"]
