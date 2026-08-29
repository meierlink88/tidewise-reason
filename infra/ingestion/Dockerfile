FROM python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ontology/requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && useradd --create-home --uid 10001 reason \
    && mkdir -p /var/lib/tidewise-reason \
    && chown reason:reason /var/lib/tidewise-reason

COPY --chown=reason:reason ingestion ./ingestion
COPY --chown=reason:reason analysis ./analysis
COPY --chown=reason:reason ontology ./ontology
COPY --chown=reason:reason projection ./projection
COPY --chown=reason:reason reasoning ./reasoning

USER reason

EXPOSE 8890
CMD ["uvicorn", "ingestion.main:app", "--host", "0.0.0.0", "--port", "8890", "--workers", "1"]
