# Arquitectura Técnica – MigPAL MVP (Piloto EUA)

## 1. Visión General
```
Telegram Bot ─────▶ Backend Orquestador (FastAPI)
                        │
                        ├── Motor IA (Ollama + Tooling)
                        ├── Pipelines Scraping / RAG
                        ├── Servicios OCR + Formularios
                        └── Panel Admin (Web)
```
- **Cliente principal:** Bot de Telegram para usuarios finales.
- **Backend:** expone APIs REST/GraphQL para bot, panel y servicios internos.
- **IA:** Ollama con modelo open-source, extendido con funciones para RAG, scraping, OCR, generación documental.
- **Persistencia:** Base relacional (PostgreSQL) + vector store (p.ej. Qdrant) + almacenamiento de documentos (S3-compatible).
- **Infraestructura:** Contenedores Docker (backend, scrapers, RAG workers, Ollama), orquestación en Docker Compose / Kubernetes (según escala).

## 2. Componentes Principales
1. **Telegram Bot Service**
   - Webhook/Long polling → mensajes.
   - Maneja comandos y enruta al backend.
   - Adjunta archivos (documentos para OCR).

2. **API Gateway / Backend Orquestador**
   - Autenticación de usuarios y admins.
   - Gestión de sesiones y contexto del roadmap.
   - Endpoints para:
     - Perfil/Assessment.
     - Roadmap y checklist.
     - Documentos (subida, OCR, revisión).
     - Simulaciones y entrevistas.
     - Métricas y scoring.
   - Coordina con microservicios internos (RAG, OCR, IA, scraping).

3. **Motor IA (Ollama + Tooling)**
   - Modelo base seleccionado (Llama 3, Mixtral, etc.).
   - Herramientas conectadas:
     - `rag_query` (consulta a vector store).
     - `web_scrape` (invoca scrapers/ETL).
     - `ocr_process`.
     - `form_generate` (PDF/Docx templates).
     - `probability_score`.
     - `simulation_engine`.
   - Prompt manager para contextos específicos (legal, vivienda, negocio).

4. **Pipelines Scraping / RAG**
   - Workers que ejecutan scraping (legal, vivienda, rankings, etc.).
   - ETL → normalización → embeddings → vector store.
   - Scheduler (Celery/Temporal) para periodicidad.
   - Monitoreo de calidad de datos (logs, alertas).

5. **OCR Service**
   - API interna que usa la librería seleccionada (según evaluación) y retorna JSON estructurado.
   - Soporta múltiples idiomas y tipos de documentos.
   - Enruta a almacenamiento y engancha con generación de formularios.

6. **Form & Document Generator**
   - Plantillas (Jinja2, LaTeX, Docx) para formularios USCIS, cartas, contratos.
   - Workflow de revisión: borrador → feedback → versión final.
   - Integración con firma electrónica (DocuSign/HelloSign) para aprobación final.

7. **Probability & Scoring Engine**
   - Regla base por tipo de proceso (visa, trámite).
   - Variables: cumplimiento requisitos, antecedentes, calidad documental, historial.
   - IA puede ajustar score según insights (ej. missing docs, riesgos).
   - Expuesto como microservicio consultable.

8. **Panel Administrativo (Web)**
   - Autenticación admin.
   - Tableros de usuarios, estatus, formularios en progreso, simulaciones.
   - Control manual de scraping y fuentes.
   - Visualización de métricas (aprobaciones, tiempos, satisfacción).

9. **Persistencia**
   - **Base relacional (PostgreSQL):** usuarios, assessments, roadmap, documentos (metadatos), simulaciones, logs.
   - **Vector store (Qdrant/Weaviate):** embeddings de documentos legales, FAQ, contenido scraped.
   - **Almacenamiento de archivos (S3 MinIO):** documentos originales, versiones generadas, contratos firmados.

10. **Observabilidad y Seguridad**
- Logs centralizados (ELK/Datadog) para bot, backend y scrapers.
- Alertas de scraping fallido o fuentes desactualizadas.
- Monitoreo de salud de Ollama y workers.
- Cifrado de datos sensibles y cumplimiento (PII).
- Auditoría de accesos (especialmente para documentos y firmas).

## 3. Flujos Clave
### 3.1 Perfil & Assessment
```
Usuario Telegram → Bot → Backend (assessment API) → DB
Backend → IA (generar resumen/roadmap) → almacena
```

### 3.2 Roadmap & Checklist
```
Bot solicita roadmap → Backend → IA + Regla → responde al usuario y actualiza DB
Usuario marca tarea completada → Backend actualiza estado y recalcula timeline
```

### 3.3 Documentos & OCR
```
Usuario envía documento → Bot → Storage
Backend llama `OCR Service` → resultados a DB
IA revisa y solicita faltantes/correcciones
Generación de formulario → revisión → firma
```

### 3.4 Simulaciones
```
Usuario pide simulación → IA lanza escenario (script)
Respuestas guardadas → Evaluation engine produce feedback
```

### 3.5 Scraping & RAG
```
Scheduler activa scraper → datos crudos → ETL → Vector Store
IA (via tool) consulta `rag_query` para responder preguntas legales/actualizadas
```

## 4. Consideraciones de Infraestructura
- **Despliegue:** Docker Compose en desarrollo, migrar a Kubernetes/ECS para producción.
- **Servidores dedicados:**
  - Ollama requiere GPU/CPU dedicados según modelo.
  - Scrapers pueden ejecutarse en workers separados.
- **Escalabilidad:**
  - API backend autoescalable (horizontal).
  - Vector store y almacenamiento escalables.
- **Seguridad:**
  - Encriptar PII en reposo.
  - Endpoints internos protegidos (mTLS y tokens internos).
  - Gestión de secretos (Vault/SSM).

## 5. Extensiones Futuras (Post-MVP)
1. **Comunidad estilo red social para migrantes:**
   - Microservicio social (posts, grupos, eventos, moderación).
   - Integración con roadmap (ej. foros por visa/ciudad).
2. **Marketplace de productos/servicios:**
   - Catálogo, pagos, reputación.
   - Segmentos: productos de migrantes, servicios profesionales, finca raíz/alquileres.
3. **Audio/Video y Apps móviles.**
4. **Automatizaciones avanzadas:** IA multiagente, flujos sin intervención, integración con CRMs.

## 6. Próximos Entregables Técnicos
- Diagramas detallados (C4, secuencia, BPMN para formularios).
- Especificación de endpoints y contratos API.
- Evaluación de modelos Ollama y OCR (documentada).
- Scripts base de scraping y pipeline RAG.
- Prototipo del bot de Telegram conectado al backend.

---
Este documento establece el blueprint para implementar el MVP de MigPAL con énfasis en la integración de IA (Ollama), scraping, RAG, OCR y automatización del proceso migratorio. Sienta las bases para las funcionalidades sociales y marketplace en etapas posteriores.
