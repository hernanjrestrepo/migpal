# Pipeline RAG – MigPAL

## Objetivo
Construir un sistema de Retrieval-Augmented Generation desde cero para proveer contexto legal, de vivienda, negocio y otros aspectos migratorios actualizado y verificable.

## Etapas del Pipeline
1. **Descubrimiento & Catálogo de Fuentes**
   - Lista priorizada de URLs/APIs por categoría (legal, vivienda, educación, etc.).
   - Metadata: frecuencia de cambio, formato (HTML/PDF/JSON), condiciones de uso.

2. **Ingesta / Scraping**
   - Scrapers específicos por fuente (BeautifulSoup, Playwright, APIs).
   - Extracción incremental (detecta cambios para no reprocesar todo).
   - Manejo de rate limits y bloqueo.

3. **Normalización & Limpieza**
   - Conversión a texto plano, preservando estructura semántica.
   - Extracción de tablas/listas a formatos estructurados.
   - Enriquecimiento con metadatos (fecha, tipo doc, jurisdicción).

4. **Segmentación (Chunking)**
   - Heurísticas basadas en secciones legales, headings, bullet points.
   - Tamaño objetivo configurable (ej. 500-800 tokens).
   - Asociar cada chunk con su origen y versión.

5. **Embeddings**
   - Selección de modelo open source (E5, Instructor, BGE) compatible con despliegue local.
   - Procesamiento batch con GPU cuando sea posible.

6. **Almacenamiento Vectorial**
   - Qdrant/Chroma/Weaviate con replicación y backups.
   - Metadata searchable (fuente, fecha, etiquetas).
   - APIs internas para consultas semánticas.

7. **Servicio de Consulta RAG**
   - Endpoint unificado que recibe query + contexto (usuario, proceso).
   - Realiza búsqueda semántica + re-ranking.
   - Retorna snippets + referencias (URL, sección). Obligatorio mostrar fuente para trazabilidad.

8. **Actualización & Monitoreo**
   - Schedulers (Celery/Temporal) para ejecutar scraping según frecuencia.
   - Alertas de fallos, cambios en estructura HTML, errores de autenticación.
   - Versionado de documentos para auditoría legal.

## Integración con IA (Ollama)
- El modelo invoca `rag_query` para acceder al contexto relevante antes de responder.
- El prompt incluye instructivo para citar fuentes y evitar alucinaciones.
- Posible uso de "hybrid search" (BM25 + embeddings) para precisión en textos legales.

## Roadmap de Implementación
1. Catalogar fuentes y priorizar (USCIS, DOS, state.gov, etc.).
2. Desarrollar scrapers MVP para top 5 fuentes críticas.
3. Construir pipeline ETL + vector store básico.
4. Integrar servicio RAG con backend/IA.
5. Escalar cobertura a vivienda, negocio, educación.
6. Añadir monitoreo y re-scraping automático.
