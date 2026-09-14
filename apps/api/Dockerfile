# Reality api — built from the REPOSITORY ROOT, never from apps/api/:
#   docker buildx build --platform linux/amd64 -f apps/api/Dockerfile \
#     -t <account-id>.dkr.ecr.<region>.amazonaws.com/<repository>:api-<sha> .
#
# --platform linux/amd64 is mandatory. Both Karpenter NodePools in the target
# cluster pin kubernetes.io/arch=amd64 and the managed group is
# AL2023_x86_64_STANDARD, so there is no arm64 capacity. An image built on
# Apple Silicon without --platform CrashLoopBackOffs with "exec format error".

# ---------------------------------------------------------------- build stage
FROM python:3.12-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /src

# Dependencies are installed from pyproject's dependency list alone, before the
# source is copied, so editing Python code does not re-resolve the whole
# dependency tree on every build.
#
# NOTE: pyproject.toml pins only lower bounds (">=") and the repo ships no lock
# file, so two builds of the same git SHA can resolve different versions. Adding
# a uv/pip-tools lock file is the right follow-up; until then, rely on the
# immutable ECR tag to pin what actually shipped.
COPY packages/reality-core/pyproject.toml ./
RUN python -c "import tomllib;print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/requirements.txt \
 && python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install -r /tmp/requirements.txt

COPY packages/reality-core/src ./src
COPY packages/reality-core/migrations ./migrations
COPY packages/reality-core/config ./config
COPY packages/reality-core/fixtures ./fixtures
COPY packages/reality-core/storylines ./storylines
RUN /opt/venv/bin/pip install --no-deps .

# -------------------------------------------------------------- runtime stage
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    REALITY_ROOT=/app/packages/reality-core

# REALITY_ROOT is load-bearing in three places, so the files below must stay at
# this path:
#   reality.db.core.init_db()     -> $REALITY_ROOT/alembic.ini, $REALITY_ROOT/migrations
#   reality.security.secrets      -> $REALITY_ROOT/.reality-secret.key (fallback Fernet key)
#   reality.services.artifacts    -> $REALITY_ROOT/data/artifacts (default artifact dir)
#
# Always set REALITY_MASTER_KEY in the cluster. Without it the first tenant
# credential write silently succeeds — this directory is writable by UID 1001 —
# and produces a PER-POD ephemeral Fernet key, so every restart orphans every
# previously stored tenant secret. Setting REALITY_ENV=production (which the
# Helm chart does) turns that silent fallback into a hard RuntimeError instead.

WORKDIR /app/packages/reality-core

COPY --from=build /opt/venv /opt/venv

# Release identity, set by the publish workflow; "dev" for a local build.
ARG REALITY_VERSION=dev
ARG REALITY_COMMIT=
ENV REALITY_VERSION=${REALITY_VERSION} \
    REALITY_COMMIT=${REALITY_COMMIT}
LABEL org.opencontainers.image.source="https://github.com/Xentral-Labs/reality" \
      org.opencontainers.image.version="${REALITY_VERSION}" \
      org.opencontainers.image.revision="${REALITY_COMMIT}" \
      org.opencontainers.image.licenses="MIT"

# alembic.ini and migrations/ are resolved from REALITY_ROOT by init_db() and by
# the `alembic upgrade head` the migration Job runs from this WORKDIR. config/ is
# checked at REALITY_ROOT/config before the packaged copy. fixtures/ is carried
# for parity with the compose image only — reality.demo resolves it relative to
# the installed package, not from here.
COPY packages/reality-core/alembic.ini ./
COPY packages/reality-core/migrations ./migrations
COPY packages/reality-core/config ./config
COPY packages/reality-core/fixtures ./fixtures

# A login shell (`kubectl exec -it ... -- bash -l`) resets PATH from /etc/profile
# and would lose /opt/venv/bin, leaving no python, alembic, uvicorn or reality.
RUN printf 'PATH=/opt/venv/bin:$PATH\nexport PATH\n' > /etc/profile.d/venv.sh

# `reality tenant use` writes its tenant-context file to a data/ directory that
# reality.cli.context resolves from the INSTALL PREFIX, not from REALITY_ROOT —
# so that path lands inside the venv and must be writable by the runtime user.
RUN groupadd --gid 1001 reality \
 && useradd --uid 1001 --gid 1001 --home-dir /home/reality --create-home \
      --shell /bin/bash reality \
 && mkdir -p /opt/venv/lib/python3.12/data /app/packages/reality-core/data/artifacts \
 && chown -R 1001:1001 /app /home/reality /opt/venv/lib/python3.12/data

USER 1001:1001

EXPOSE 8000

CMD ["uvicorn", "--no-access-log", "reality.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
