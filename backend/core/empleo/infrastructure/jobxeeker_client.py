"""
Empleo — infrastructure: cliente HTTP real contra JobXeeker (Sprint 10b,
Hito 5).

Contrato verificado en vivo el 6 sept 2026 contra una instancia local
(`JOBXEEKER_BASE_URL`) -- registro, `PUT /api/profiles/{user_id}` (no
`POST /api/profiles/`, que crea un perfil sin reclamar, no el propio),
matching y refresh, de punta a punta antes de escribir este archivo.

Hallazgo real, no inventado: `POST /api/matches/run/{user_id}` puede
devolver `success: false, analysis_status: "degraded_mode"` con un error
interno de JobXeeker (`'<' not supported between instances of 'NoneType'
and 'float'`) -- un bug del lado de JobXeeker, no de esta integración.
Este cliente no lo esconde: lo propaga tal cual en el resultado para que
`application/handlers.py` decida qué mostrarle al usuario."""

from __future__ import annotations

import os

import httpx

# Mismo criterio que ADAN (ver core/negocio/infrastructure/adan_client.py):
# `host.docker.internal`, no `localhost`, porque el backend de MigPAL
# corre en un contenedor Docker distinto de donde corre JobXeeker.
JOBXEEKER_BASE_URL = os.getenv("JOBXEEKER_BASE_URL", "http://host.docker.internal:8012")
JOBXEEKER_TIMEOUT_SECONDS = float(os.getenv("JOBXEEKER_TIMEOUT_SECONDS", "30"))


class JobXeekerIntegrationError(RuntimeError):
    """JobXeeker respondió con error, o no respondió."""


class JobXeekerClient:
    def __init__(self, base_url: str = JOBXEEKER_BASE_URL) -> None:
        self._base_url = base_url

    async def register(self, *, email: str, password: str, name: str) -> tuple[str, str, str]:
        """Devuelve (access_token, refresh_token, user_id)."""
        async with httpx.AsyncClient(base_url=self._base_url, timeout=JOBXEEKER_TIMEOUT_SECONDS) as client:
            resp = await client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
        if resp.status_code != 200:
            raise JobXeekerIntegrationError(f"JobXeeker rechazó el registro ({resp.status_code}): {resp.text}")
        body = resp.json()
        return body["access_token"], body["refresh_token"], body["user_id"]

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        """El refresh token rota -- devuelve (access_token, refresh_token_nuevo)."""
        async with httpx.AsyncClient(base_url=self._base_url, timeout=JOBXEEKER_TIMEOUT_SECONDS) as client:
            resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        if resp.status_code != 200:
            raise JobXeekerIntegrationError(f"JobXeeker rechazó el refresh ({resp.status_code}): {resp.text}")
        body = resp.json()
        return body["access_token"], body["refresh_token"]

    async def update_profile(
        self,
        *,
        access_token: str,
        user_id: str,
        name: str,
        email: str,
        target_roles: list[str],
        target_industries: list[str],
        location_preference: str | None,
        experience_level: str | None,
        skills: list[str],
    ) -> None:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=JOBXEEKER_TIMEOUT_SECONDS) as client:
            resp = await client.put(
                f"/api/profiles/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "name": name, "email": email, "target_roles": target_roles,
                    "target_industries": target_industries, "location_preference": location_preference,
                    "experience_level": experience_level, "skills": skills,
                },
            )
        if resp.status_code != 200:
            raise JobXeekerIntegrationError(f"JobXeeker rechazó el perfil ({resp.status_code}): {resp.text}")

    async def run_matches(self, *, access_token: str, user_id: str) -> dict:
        """No lanza si JobXeeker responde `success: false` (degraded_mode,
        ver docstring del módulo) -- eso es un resultado válido, no un
        fallo de transporte. Solo lanza si la llamada HTTP en sí falla."""

        async with httpx.AsyncClient(base_url=self._base_url, timeout=JOBXEEKER_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"/api/matches/run/{user_id}", headers={"Authorization": f"Bearer {access_token}"})
        if resp.status_code != 200:
            raise JobXeekerIntegrationError(f"JobXeeker rechazó correr el matching ({resp.status_code}): {resp.text}")
        return resp.json()

    async def list_matches(self, *, access_token: str, user_id: str) -> list[dict]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=JOBXEEKER_TIMEOUT_SECONDS) as client:
            resp = await client.get(
                "/api/matches/", headers={"Authorization": f"Bearer {access_token}"}, params={"user_id": user_id}
            )
        if resp.status_code != 200:
            raise JobXeekerIntegrationError(f"JobXeeker rechazó listar matches ({resp.status_code}): {resp.text}")
        return resp.json()
