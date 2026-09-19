FROM python:3.12-slim AS catalogs
WORKDIR /repo
COPY packages/reality-core/pyproject.toml packages/reality-core/pyproject.toml
COPY packages/reality-core/src packages/reality-core/src
COPY packages/reality-core/config packages/reality-core/config
COPY packages/reality-core/fixtures packages/reality-core/fixtures
COPY packages/reality-core/storylines packages/reality-core/storylines
COPY packages/reality-core/migrations packages/reality-core/migrations
COPY apps/docs/scripts/generate-catalog-reference.py apps/docs/scripts/data_model_reference.py apps/docs/scripts/analytics_model_reference.py apps/docs/scripts/
COPY apps/docs/content apps/docs/content
RUN python -m pip install --no-cache-dir ./packages/reality-core \
    && PYTHONPATH=packages/reality-core/src python apps/docs/scripts/generate-catalog-reference.py

FROM node:22-alpine AS build
WORKDIR /app
ARG APP_URL=https://app.runreality.ai
ARG SITE_URL=https://runreality.ai
ARG DOCS_URL=https://docs.runreality.ai
ARG ANALYTICS_SCRIPT_URL=
ARG ANALYTICS_WEBSITE_ID=
ENV APP_URL=${APP_URL} \
    SITE_URL=${SITE_URL} \
    DOCS_URL=${DOCS_URL} \
    ANALYTICS_SCRIPT_URL=${ANALYTICS_SCRIPT_URL} \
    ANALYTICS_WEBSITE_ID=${ANALYTICS_WEBSITE_ID}
COPY apps/docs/package*.json ./
RUN npm ci
COPY apps/docs/ .
COPY apps/shared/ /shared/
COPY --from=catalogs /repo/apps/docs/content/tool-usage ./content/tool-usage
COPY --from=catalogs /repo/apps/docs/content/de/tool-usage ./content/de/tool-usage
COPY --from=catalogs /repo/apps/docs/.vitepress/data ./.vitepress/data
RUN npm run build

FROM nginx:1.27-alpine
COPY apps/docs/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/.vitepress/dist /usr/share/nginx/html
EXPOSE 80
