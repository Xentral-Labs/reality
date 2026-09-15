FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REALITY_ROOT=/app/packages/reality-core

WORKDIR /app/packages/reality-core

# Release identity, set by the publish workflow; "dev" for a local build.
ARG REALITY_VERSION=dev
ARG REALITY_COMMIT=
ENV REALITY_VERSION=${REALITY_VERSION} \
    REALITY_COMMIT=${REALITY_COMMIT}
LABEL org.opencontainers.image.source="https://github.com/Xentral-Labs/reality" \
      org.opencontainers.image.version="${REALITY_VERSION}" \
      org.opencontainers.image.revision="${REALITY_COMMIT}" \
      org.opencontainers.image.licenses="MIT"

COPY packages/reality-core/pyproject.toml ./
COPY packages/reality-core/src ./src
COPY packages/reality-core/migrations ./migrations
COPY packages/reality-core/config ./config
COPY packages/reality-core/fixtures ./fixtures
COPY packages/reality-core/storylines ./storylines
COPY packages/reality-core/alembic.ini ./

RUN pip install --no-cache-dir .

CMD ["reality-worker", "work", "--poll-seconds", "1"]
