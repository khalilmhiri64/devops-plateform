FROM nginxinc/nginx-unprivileged:1.27-alpine
ARG VERSION=dev
LABEL org.opencontainers.image.title="jobs-frontend" org.opencontainers.image.version=$VERSION
# API_UPSTREAM / DNS_RESOLVER are substituted by the official image's envsubst entrypoint.
ENV API_UPSTREAM=http://api:8000 DNS_RESOLVER=127.0.0.11
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY public/ /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
