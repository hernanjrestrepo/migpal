"""
Negocio — infrastructure: cliente HTTP real contra ADAN (Sprint 10, Hito 5).

Contrato verificado en vivo contra la instancia real corriendo en
`ADAN_BASE_URL` (puerto 8050 en este entorno) el 6 sept 2026 -- no es un
contrato inventado desde la documentación: se probó
registro -> login -> crear compañía -> chat -> board-room de punta a
punta antes de escribir este archivo. `board-room` exige que exista al
menos un mensaje de chat previo en la compañía ("No hay descripción del
dolor. Inicia una conversación primero." -- error real devuelto por ADAN)
y su respuesta no tiene un schema fijo (llega `{}` en su propio OpenAPI),
así que acá se navega con `.get()` defensivo, nunca asumiendo una forma
exacta -- ADAN mismo está en consolidación (WO-090) y su formato puede
cambiar.

Cliente sin estado -- no cachea nada, cada método hace su propia llamada.
El manejo de "¿tengo un token vigente o necesito loguearme de nuevo?" vive
en `application/handlers.py`, no acá."""

from __future__ import annotations

import os

import httpx

# `host.docker.internal` -- no `localhost` -- porque el backend de MigPAL
# corre dentro de un contenedor Docker; `localhost` ahí apunta al propio
# contenedor, no al host donde corre ADAN. Docker Desktop resuelve ese
# nombre al host automáticamente (Windows/Mac); en un entorno sin Docker
# Desktop (Linux nativo) hay que fijar `ADAN_BASE_URL` explícito.
ADAN_BASE_URL = os.getenv("ADAN_BASE_URL", "http://host.docker.internal:8050")
ADAN_TIMEOUT_SECONDS = float(os.getenv("ADAN_TIMEOUT_SECONDS", "90"))


class AdanIntegrationError(RuntimeError):
    """ADAN respondió con un error, o no respondió -- nunca se confunde
    con `NegocioInvariantError` (eso es una regla de negocio de MigPAL,
    esto es "el sistema externo falló")."""


class AdanClient:
    def __init__(self, base_url: str = ADAN_BASE_URL) -> None:
        self._base_url = base_url

    async def register(self, *, email: str, name: str, password: str) -> tuple[str, str]:
        """Devuelve (access_token, adan_user_id). ADAN responde 201 acá
        (creación de recurso) -- verificado en vivo, no 200 como su propio
        OpenAPI schema sugiere; se acepta cualquiera de los dos por si esto
        cambia entre versiones de ADAN."""

        async with httpx.AsyncClient(base_url=self._base_url, timeout=ADAN_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                "/api/v1/auth/register", json={"email": email, "name": name, "password": password}
            )
        if resp.status_code not in (200, 201):
            raise AdanIntegrationError(f"ADAN rechazó el registro ({resp.status_code}): {resp.text}")
        body = resp.json()
        return body["access_token"], body["user"]["id"]

    async def login(self, *, email: str, password: str) -> str:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=ADAN_TIMEOUT_SECONDS) as client:
            resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        if resp.status_code != 200:
            raise AdanIntegrationError(f"ADAN rechazó el login ({resp.status_code}): {resp.text}")
        return resp.json()["access_token"]

    async def create_company(
        self, *, access_token: str, name: str, description: str, industry: str | None, country: str | None
    ) -> str:
        """Devuelve el company_id (UUID de ADAN)."""
        async with httpx.AsyncClient(base_url=self._base_url, timeout=ADAN_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                "/api/v1/companies/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"name": name, "description": description, "industry": industry, "country": country},
            )
        if resp.status_code not in (200, 201):
            raise AdanIntegrationError(f"ADAN rechazó crear la compañía ({resp.status_code}): {resp.text}")
        return resp.json()["id"]

    async def send_chat_message(self, *, access_token: str, company_id: str, message: str) -> None:
        """El Board Room exige una conversación previa -- este método
        establece/actualiza esa conversación. No se usa la respuesta del
        chat en sí (eso lo consume el usuario en ADAN, no en MigPAL)."""

        async with httpx.AsyncClient(base_url=self._base_url, timeout=ADAN_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"/api/v1/nivel1/{company_id}/chat",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"message": message},
            )
        if resp.status_code != 200:
            raise AdanIntegrationError(f"ADAN rechazó el mensaje ({resp.status_code}): {resp.text}")

    async def run_board_room(self, *, access_token: str, company_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=ADAN_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"/api/v1/nivel1/{company_id}/board-room",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code != 200:
            raise AdanIntegrationError(f"ADAN rechazó correr el Board Room ({resp.status_code}): {resp.text}")
        return resp.json()
