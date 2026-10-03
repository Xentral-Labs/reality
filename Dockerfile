FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REALITY_ROOT=/app/packages/reality-core

WORKDIR /app/packages/reality-core

COPY packages/reality-core/pyproject.toml ./
ARG REALITY_COMMIT=
ENV REALITY_COMMIT=${REALITY_COMMIT} REALITY_BLUEPRINT_EVIDENCE=/opt/blueprint-evidence
COPY scripts/package_business_blueprint_evidence.py /tmp/package_business_blueprint_evidence.py
COPY packages/reality-core/tests /tmp/blueprint-tests
RUN python /tmp/package_business_blueprint_evidence.py --source /tmp/blueprint-tests --output /opt/blueprint-evidence --commit "${REALITY_COMMIT}"
COPY packages/reality-core/src ./src
COPY packages/reality-core/migrations ./migrations
COPY packages/reality-core/config ./config
COPY packages/reality-core/fixtures ./fixtures
COPY packages/reality-core/storylines ./storylines
COPY packages/reality-core/alembic.ini ./

RUN pip install --no-cache-dir .

CMD ["/bin/sh", "-c", "case \"${REALITY_BACKGROUND_ROLE:-}\" in scheduler) exec reality-scheduler work --poll-seconds 5 ;; worker) exec reality-worker work --poll-seconds 5 ;; *) echo 'REALITY_BACKGROUND_ROLE must be scheduler or worker.' >&2; exit 64 ;; esac"]
