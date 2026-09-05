"""
Middleware transversal de producción: cabeceras de seguridad, request-id y
rate limiting.

Nada de esto es lógica de negocio -- por eso vive en `app/`, no en ningún
bounded context de `core/`. Los bounded contexts no saben que existe.

Decisiones deliberadas:

- **Rate limit en memoria, no en Redis.** El backend corre hoy como un solo
  proceso (`uvicorn main:app`, ver docker-compose.yml). Un contador en
  memoria protege exactamente el modo de abuso real de esta etapa: fuerza
  bruta contra `/auth/token` desde un cliente. Cuando haya más de una
  réplica, esto deja de ser suficiente y hay que moverlo a Redis (ya está
  en el stack) -- está marcado abajo y en docs/DEPLOYMENT.md, no escondido.
- **Solo se limitan los endpoints de autenticación.** Limitar todo el API
  sin datos de uso real produciría cortes arbitrarios a usuarios legítimos.
  Login y registro son los que tienen un abuso obvio y conocido.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Rutas protegidas contra fuerza bruta y su cupo por ventana.
_RATE_LIMITED_PATHS: dict[str, tuple[int, int]] = {
    # ruta: (máximo de intentos, ventana en segundos)
    "/api/v1/auth/token": (10, 60),
    "/v1/auth/register": (5, 300),
}

# ip -> path -> timestamps de los intentos dentro de la ventana
_hits: dict[str, dict[str, deque[float]]] = defaultdict(lambda: defaultdict(deque))


def _client_ip(request: Request) -> str:
    """IP real detrás del reverse proxy. `X-Forwarded-For` puede venir con
    una cadena de proxies: el primero es el cliente original."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Ventana deslizante por (IP, ruta). Ver nota del módulo sobre por qué
    es en memoria y cuándo deja de alcanzar."""

    async def dispatch(self, request: Request, call_next):
        limit = _RATE_LIMITED_PATHS.get(request.url.path)
        if limit is None or request.method != "POST":
            return await call_next(request)

        max_hits, window = limit
        now = time.monotonic()
        bucket = _hits[_client_ip(request)][request.url.path]

        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= max_hits:
            retry_after = int(window - (now - bucket[0])) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": f"Demasiados intentos. Probá de nuevo en {retry_after} segundos."},
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Cabeceras de seguridad estándar.

    No se fija `Content-Security-Policy` acá: el frontend lo sirve nginx
    (ver deploy/nginx.conf), que es donde tiene sentido definir la política
    de la página. Ponerla en las respuestas JSON del API no aporta nada."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Correlaciona una petición con sus logs. Respeta el `X-Request-ID` que
    venga del proxy en vez de generar uno nuevo, para no romper la traza."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
