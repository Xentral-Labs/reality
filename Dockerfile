FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REALITY_ROOT=/app/packages/reality-core

WORKDIR /app/packages/reality-core

COPY packages/reality-core/pyproject.toml ./
COPY packages/reality-core/src ./src
COPY packages/reality-core/migrations ./migrations
COPY packages/reality-core/config ./config
COPY packages/reality-core/fixtures ./fixtures
COPY packages/reality-core/storylines ./storylines
COPY packages/reality-core/alembic.ini ./

RUN pip install --no-cache-dir .

CMD ["/bin/sh", "-c", "case \"${REALITY_BACKGROUND_ROLE:-}\" in scheduler) exec reality-scheduler work --poll-seconds 5 ;; worker) exec reality-worker work --poll-seconds 5 ;; *) echo 'REALITY_BACKGROUND_ROLE must be scheduler or worker.' >&2; exit 64 ;; esac"]
