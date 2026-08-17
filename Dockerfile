# syntax=docker/dockerfile:1
FROM eclipse-temurin:8-jdk-jammy@sha256:b5f541356025b22031e2337b72c2d2a511bacf7eb79100acb7f107a06cacc838 AS python-deps

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        build-essential \
        ca-certificates \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/tidewise/venv \
    && /opt/tidewise/venv/bin/pip install --no-cache-dir --upgrade pip
COPY requirements/kag-runtime.lock /tmp/kag-runtime.lock
RUN /opt/tidewise/venv/bin/pip install --no-cache-dir --requirement /tmp/kag-runtime.lock
COPY .runtime/build/kag/*.whl /tmp/kag/
RUN /opt/tidewise/venv/bin/pip install --no-cache-dir --no-deps /tmp/kag/*.whl \
    && KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 /opt/tidewise/venv/bin/kag --help >/dev/null \
    && KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 /opt/tidewise/venv/bin/knext --help >/dev/null

FROM eclipse-temurin:8-jre-jammy@sha256:994dbce04a62f22f6c007fbbe2614303efa3b15668addfaa9262f8530b4b362d

ARG OPENSPG_COMMIT
ARG KAG_COMMIT
ARG OPENSPG_VERSION
ARG KAG_VERSION
ARG OPENSPG_JAR_SHA256
ARG KAG_WHEEL_SHA256
LABEL org.opencontainers.image.title="Tidewise Reason OpenSPG runtime" \
      org.opencontainers.image.source="https://github.com/meierlink88/tidewise-reason" \
      io.tidewise.openspg.version="${OPENSPG_VERSION}" \
      io.tidewise.openspg.commit="${OPENSPG_COMMIT}" \
      io.tidewise.openspg.jar.sha256="${OPENSPG_JAR_SHA256}" \
      io.tidewise.kag.version="${KAG_VERSION}" \
      io.tidewise.kag.commit="${KAG_COMMIT}" \
      io.tidewise.kag.wheel.sha256="${KAG_WHEEL_SHA256}"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PATH=/opt/tidewise/venv/bin:$PATH \
    KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 \
    PYTHON_EXEC=/opt/tidewise/venv/bin/python \
    PYTHON_PATHS=/opt/tidewise/venv/lib/python3.10/site-packages/
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates python3 \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=python-deps /opt/tidewise/venv /opt/tidewise/venv
COPY .runtime/build/openspg/*.jar /opt/openspg/arks-sofaboot-executable.jar

WORKDIR /opt/openspg
EXPOSE 8887
HEALTHCHECK --interval=10s --timeout=5s --start-period=60s --retries=30 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8887/actuator/health', timeout=3)" || exit 1
CMD ["java", "-Dfile.encoding=UTF-8", "-Xms2048m", "-Xmx8192m", "-jar", "arks-sofaboot-executable.jar"]
