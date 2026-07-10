# 📋 Checklist de Test Manual en Telegram

## Requisitos Previos

- [ ] Bot corriendo en producción
- [ ] Acceso a cuenta de Telegram de prueba
- [ ] Conexión a internet estable

## Plan Maestro - Flujo Completo

### 1. Inicio y Bienvenida
- [ ] Enviar `/start`
- [ ] Verificar mensaje de bienvenida
- [ ] Verificar botones de idioma

### 2. Selección de Idioma
- [ ] Seleccionar idioma (español)
- [ ] Verificar que el bot responde en español

### 3. Recolección de Datos Personales
- [ ] Dar nombre completo
- [ ] Dar nacionalidad
- [ ] Dar edad
- [ ] Dar profesión
- [ ] Verificar que el bot extrae los datos correctamente

### 4. Información Familiar
- [ ] Indicar estado civil
- [ ] Indicar si viaja con familia
- [ ] Dar detalles de familiares (si aplica)

### 5. Información Financiera
- [ ] Indicar ahorros
- [ ] Indicar ingresos mensuales
- [ ] Verificar que el bot entiende montos

### 6. Motivo de Migración
- [ ] Explicar razón de migración
- [ ] Indicar timeline deseado
- [ ] Verificar comprensión del bot

### 7. Resumen y Confirmación
- [ ] Verificar que el bot muestra resumen
- [ ] Confirmar que los datos son correctos
- [ ] Si hay error, corregir y verificar que el bot actualiza

### 8. Recomendación de Visa
- [ ] Verificar que el bot recomienda visa apropiada
- [ ] Verificar que explica requisitos
- [ ] Verificar que no recomienda sin datos completos

### 9. Selección de Ciudad
- [ ] Ver opciones de ciudades
- [ ] Seleccionar ciudad de interés
- [ ] Verificar información de la ciudad

### 10. Plan de Acción
- [ ] Verificar que el bot genera plan de acción
- [ ] Verificar pasos claros y accionables
- [ ] Verificar timeline realista

## Pruebas de Robustez

### Correcciones
- [ ] Dar información incorrecta
- [ ] Corregir con "no, en realidad es..."
- [ ] Verificar que el bot actualiza

### Off-topic
- [ ] Enviar mensaje off-topic
- [ ] Verificar que el bot redirige amablemente

### Errores de Escritura
- [ ] Enviar mensaje con typos
- [ ] Verificar que el bot entiende

### Silencio
- [ ] Esperar 30 segundos sin responder
- [ ] Verificar que el bot envía recordatorio

### Comandos
- [ ] Probar `/help`
- [ ] Probar `/resumen`
- [ ] Probar `/reiniciar`

## Criterios de Aprobación

- [ ] **0 crashes**: El bot nunca se cae
- [ ] **0 silencios**: El bot siempre responde
- [ ] **Flujo completo**: Se puede completar el Plan Maestro
- [ ] **Correcciones funcionan**: El bot acepta correcciones
- [ ] **Datos correctos**: El resumen refleja lo dicho

## Registro de Evidencia

Después de completar el test:

```bash
cd /workspace/hjrm/migpal/backend
python3 scripts/register_manual_test.py
```

Ingresar:
- Chat ID del usuario de prueba
- Notas sobre el test

## Notas del Tester

```
Fecha: _______________
Tester: _______________
Chat ID: _______________
Duración: _______________

Observaciones:
_________________________________
_________________________________
_________________________________

Bugs encontrados:
_________________________________
_________________________________

Resultado: [ ] APROBADO  [ ] RECHAZADO
```
