# Reglas de trabajo – MigPAL (Gemini CLI)

## Objetivo
Trabajar exclusivamente en `/workspace/migpal` para construir el proyecto MigPAL siguiendo lo ya definido en los chats del proyecto (modelo de negocio, referidos multinivel, metas y supuestos).

## Seguridad y control
- PROHIBIDO trabajar fuera de `/workspace/migpal`.
- PROHIBIDO borrar archivos o carpetas sin autorización explícita.
- PROHIBIDO modificar/imprimir secretos (`.env`, keys, tokens). Si aparecen, detenerse.
- SIEMPRE mostrar el plan y los archivos a tocar antes de modificar.
- SIEMPRE mostrar el archivo COMPLETO cuando se modifique.

## Estilo de cambios
- Cambios pequeños, verificables y por “tickets”.
- Nada de refactors masivos sin necesidad.
- No inventar dependencias; justificar cada librería nueva.

## Ejecución y logs
- Cualquier proceso en background debe usar `nohup` y log en `/workspace/migpal/logs/`.
- Crear/usar scripts en `scripts/` para start/stop/healthcheck.
- Mantener puertos documentados en `docs/PORTS.md`.

## Verificación (Definition of Done)
Para considerar un ticket “hecho” debe existir:
- Comando reproducible para levantar el servicio.
- Healthcheck (curl/endpoint) o prueba verificable.
- Log de arranque sin errores críticos.
- README actualizado si cambia el modo de correr.

## Comunicación
- En cada paso: qué se hará, por qué, cómo se valida.
- Si algo es ambiguo, proponer la mejor decisión basada en lo ya definido en el proyecto.
