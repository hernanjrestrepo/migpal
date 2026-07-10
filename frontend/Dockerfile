# Foundation (Sprint 0): placeholder mínimo -- el frontend real (Next.js,
# Product Definition / UX Specification) se construye en Sprint 1. Esto solo
# prueba que el slot "frontend" del stack levanta y responde a health checks.
FROM nginx:1.27-alpine

COPY public/ /usr/share/nginx/html/

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:80/ || exit 1

EXPOSE 80
