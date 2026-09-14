FROM node:22-alpine AS build
WORKDIR /app
ARG DOCS_URL=https://docs.runreality.ai
ARG SITE_URL=https://runreality.ai
ENV DOCS_URL=${DOCS_URL}
ENV SITE_URL=${SITE_URL}
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ .
COPY apps/shared/ /shared/
RUN npm run build

FROM nginx:1.27-alpine
ARG REALITY_VERSION=dev
ARG REALITY_COMMIT=
LABEL org.opencontainers.image.source="https://github.com/Xentral-Labs/reality" \
      org.opencontainers.image.version="${REALITY_VERSION}" \
      org.opencontainers.image.revision="${REALITY_COMMIT}" \
      org.opencontainers.image.licenses="MIT"
ENV API_UPSTREAM=api:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1 \
    NGINX_ENVSUBST_FILTER=^(API_UPSTREAM|NGINX_LOCAL_RESOLVERS)$
COPY apps/web/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
