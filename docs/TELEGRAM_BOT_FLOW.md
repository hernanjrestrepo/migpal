# Flujo Telegram Bot – MigPAL MVP

## Objetivo
Ofrecer una experiencia conversacional completa en Telegram que cubra assessment, roadmap, checklist, documentos, simulaciones y soporte IA.

## Comandos Principales
- `/start`: bienvenida, explicación del servicio.
- `/assessment`: inicia o retoma cuestionario.
- `/roadmap`: muestra plan actual y próximos pasos.
- `/checklist`: tareas pendientes y estado.
- `/documentos`: subir/consultar documentos, disparar OCR.
- `/simulacion`: entrevista consular/laboral guiada.
- `/ayuda`: listado de funciones y acceso a soporte humano.

## Flujo de Asistencia
1. **Inicio**
   - Usuario recibe introducción y consentimiento para procesar datos.
   - Bot guarda ID de Telegram ↔ cuenta MigPAL.

2. **Assessment**
   - Preguntas secuenciales (ej. país origen, tipo visa deseada, presupuesto, familia).
   - Se almacenan respuestas en backend y se resume para IA.

3. **Generación Roadmap**
   - Backend/IA produce roadmap personalizado.
   - Bot lo presenta en secciones (etapa, tiempos, costos, requisitos, servicios sugeridos).

4. **Checklist & Notificaciones**
   - Usuario marca tareas completadas (inline buttons).
   - Bot envía recordatorios para vencimientos o nuevas tareas.

5. **Documentos & OCR**
   - Usuario adjunta archivo → Bot lo sube a backend → OCR → IA valida.
   - Bot notifica resultados, solicita correcciones o valida paso.

6. **Simulaciones**
   - Usuario elige tipo de simulación.
   - IA conduce la entrevista y evalúa respuestas.
   - Se generan reportes/feedback almacenados en backend.

7. **Asistente IA**
   - Chat libre con IA (respuestas basadas en RAG + herramientas).
   - IA puede invocar scraping, scoring, formularios y devolver resultados en chat.

## Consideraciones
- Manejo de sesiones y contexto (persistencia per user).
- Control de flujo para evitar saturación y asegurar datos completos.
- Soporte multilenguaje en mensajes (ES/EN al menos).
- Logs de conversación para auditoría (cumpliendo privacidad).

## Extensión Futuro
- Integración con audios/videos (fase posterior).
- Conectores con comunidad y marketplace cuando estén disponibles.
