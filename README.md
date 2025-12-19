# MigPAL Backend

API para gestionar el sistema de referidos multinivel de MigPAL.

## Alcance Actual (Demo Final)

Esta entrega incluye:
- API mínima segura: registro de usuarios, autenticación (login).
- Sistema de referidos base: códigos de referido, asignación de nivel inicial.
- Consulta de mis referidos.
- Documentación básica en README.
- Smoke tests para verificar funcionalidad.

**Actualmente NO incluye:** cálculo de comisiones, implementación completa de la lógica multinivel, ni frontend.

## Cómo Correr la API

1.  **Instalar dependencias:**
    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **Configurar variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto (`/workspace/migpal/.env`) con las siguientes variables. Puedes usar `backend/.env.example` como plantilla.
    ```
    AUTH_SECRET_KEY=tu_secreto_jwt_seguro
    GEMINI_API_KEY=tu_clave_api_de_gemini
    ```

3.  **Iniciar el servidor:**
    ```bash
    cd backend
    uvicorn main:app --reload
    ```
    La API estará disponible en `http://localhost:8000`.

## Endpoints Principales y Ejemplos

Las credenciales del usuario de demostración son `smoketest` / `password123`.

**1. Crear un nuevo usuario:**
```bash
curl -X POST "http://localhost:8000/api/v1/users" \
-H "Content-Type: application/json" \
-d '{"email": "smoketest@example.com", "username": "smoketest", "password": "password123"}'
```

**2. Obtener Token de Autenticación:**
```bash
curl -X POST "http://localhost:8000/api/v1/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=smoketest&password=password123"
```

**3. Ver mi perfil (requiere token):**
```bash
TOKEN="tu_access_token"
curl -X GET "http://localhost:8000/api/v1/users/me" \
-H "Authorization: Bearer $TOKEN"
```

**4. Ver mis referidos (requiere token):**
```bash
TOKEN="tu_access_token"
curl -X GET "http://localhost:8000/api/v1/users/me/referrals" \
-H "Authorization: Bearer $TOKEN"
```
