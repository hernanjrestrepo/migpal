# MigPAL MVP – Plan Técnico Integral

## 1. Alcance General
- **Enfoque del MVP:** Migración hacia Estados Unidos.
- **Canal de interacción:** Bot de Telegram con asistente IA (texto) + backend orquestador.
- **Objetivo:** Guiar al usuario de manera integral cubriendo todos los aspectos de su proceso migratorio (legal, vivienda, empleo, educación, finanzas, negocio, seguridad, etc.).
- **Tecnologías clave:** Backend FastAPI, Frontend HTML/JS (para panel administrador), IA sobre Ollama, pipelines de scraping + RAG, OCR multilingüe, generación de documentos/formularios.

## 2. Módulos Principales del MVP
| Módulo | Descripción | Dependencias |
|--------|-------------|--------------|
| Perfil & Assessment | Flujos en Telegram para captar datos personales, objetivo migratorio, presupuesto, destino, experiencia, familia. | Bot Telegram, backend usuarios. |
| Roadmap Inteligente | Motor que genera pasos, tiempos, costos, requisitos y servicios aliados. | Motor de reglas + RAG legal. |
| Scraping & RAG Legal | Pipeline para extraer datos de USCIS/DOS/leyes estatales y almacenarlos en vector store. | Scrapers, normalizadores, embeddings, DB. |
| Integraciones Vivienda/Negocio/Vida | Conectores a Zillow, Realtor, businessesforsale.com, bizbuysell.com, rankings ciudades, GreatSchools, LinkedIn Jobs, etc. | Scrapers/APIs, ETL. |
| OCR Multilingüe | Evaluar librerías y seleccionar la mejor opción para procesar documentos subidos por usuarios. | Servicios OCR, almacenamiento. |
| Generación de Formularios | Plantillas y generación automática de borradores (USCIS, cartas, contratos). Flujo de revisión + firma electrónica. | IA + renderer PDF/Docx + firma. |
| Asistente IA Ollama | Modelo open source parametrizable, con tool calling (scraping, RAG, formularios, scoring, simulaciones). | Ollama server, prompts, herramientas. |
| Simulaciones y entrenamiento | Flujos de entrevistas consulares y laborales (texto) guardando historial. | IA + base de datos. |
| Panel Administrativo | Vista web para admins (usuarios, roadmaps, métricas, fuentes). | Frontend + backend admin. |
| Métrica de Probabilidad | Esquema de scoring basado en requisitos vs. cumplimiento, antecedentes, datos históricos. | Motor de reglas + IA + datos públicos. |

## 3. Fuentes y Conectores
- **Leyes migratorias/estatales:** USCIS, DOS, Code of Federal Regulations, state.gov, law.cornell.edu, travel.state.gov.
- **Vivienda:** Zillow, Realtor.com, Apartments.com (priorizar APIs oficiales; fallback scraping con respeto a ToS).
- **Negocios:** businessesforsale.com, bizbuysell.com.
- **Ranking ciudades/calidad de vida:** BestPlaces, Livability, Numbeo, US Census API.
- **Educación:** GreatSchools (API), Niche, CollegeScorecard (Dept. Education).
- **Empleo/Networking:** LinkedIn Jobs (posible scraping), Indeed API, Glassdoor, O*NET.
- **Seguridad/Noticias:** FBI Crime Data Explorer, city-data.com, newsapi.org.
- **Salud/Seguros:** healthcare.gov, aseguradoras privadas.

Cada fuente debe tener metadatos: URL, tipo acceso (API/scraping), frecuencia actualización, licenciamiento, endpoints clave.

## 4. Pipeline RAG desde Cero
1. **Ingesta:** Scrapers y descargadores de PDFs/HTML.
2. **Normalización:** Limpieza, extracción de tablas/listas, conversión a texto.
3. **Segmentación:** Chunking basado en semántica (párrafos, secciones legales).
4. **Embeddings:** Uso de modelo open-source (ej. Instructor, E5) compatible con Ollama o servicio local.
5. **Almacenamiento:** Vector store (Chroma, Weaviate, Qdrant) + metadata (fuente, fecha, tipo).
6. **Consulta:** API interna para el asistente IA con búsqueda semántica + filtros.
7. **Actualización:** Jobs programados (cron) para re-scrapear fuentes críticas.

## 5. Evaluación y Selección de OCR
### Candidatos:
- **Tesseract:** Libre, multi-idioma, configurable pero menor precisión en documentos complejos.
- **PaddleOCR:** Buen rendimiento, soporta múltiples idiomas, activo en comunidad.
- **AWS Textract:** Alta precisión, manejo de formularios/tablas, costo por uso.
- **Google Document AI:** Precisión destacada, múltiples idiomas, integración GCP.
- **Azure Form Recognizer:** Similar a Textract, buen soporte empresarial.

### Criterios (peso sugerido):
| Criterio | Peso |
|---------|------|
| Precisión multi-idioma | 30% |
| Manejo de formularios/tablas | 20% |
| Latencia y escalabilidad | 15% |
| Costo total | 15% |
| Facilidad de integración | 10% |
| Comunidad/Soporte | 10% |

### Plan de Evaluación:
1. Preparar dataset de documentos en distintos idiomas y formatos.
2. Correr pruebas con cada servicio y medir KPIs (precisión OCR, tiempo, costo estimado).
3. Calcular score ponderado y seleccionar la mejor opción.
4. Para MVP, se puede combinar: PaddleOCR (on-prem) + servicio cloud para casos complejos.

## 6. Automatización de Formularios y Firma Electrónica
- **Workflow:**
  1. IA solicita información pendiente al usuario vía Telegram.
  2. Genera borradores (PDF/Docx) de formularios USCIS, cartas de explicación, contratos.
  3. Usuario revisa y envía comentarios.
  4. IA actualiza y produce versión final.
  5. Integrar servicio de firma electrónica (DocuSign/HelloSign) para minimizar fricción.
- **Métricas & Scoring:**
  - Cada proceso (visa, trámite) tendrá checklist de requisitos obligatorios/opcionales.
  - El sistema calcula probabilidad de aprobación basada en cumplimiento, antecedentes, calidad documental, estadísticas históricas.
  - El motor puede proponer acciones correctivas (ej. “Falta traducir certificado X”).

## 7. Modelo IA en Ollama
- **Requisitos:**
  - Razonamiento jurídico/administrativo.
  - Multi-idioma.
  - Ventana de contexto amplia (>32K tokens idealmente).
  - Compatible con tool calling (extensiones vía backend).
- **Candidatos:** Llama 3, Mixtral 8x7B, Qwen 2, Phi-3, etc. Se evaluará desempeño en pruebas de prompts reales.
- **Herramientas conectadas:**
  - RAG (consulta legal y factual).
  - Scraping (disparar jobs y resumir).
  - OCR (procesar documentos).
  - Form generation (PDF/Docx templates).
  - Scoring de probabilidad.
  - Simulaciones (entrevistas) y evaluación textual.

## 8. Simulaciones y Entrenamiento
- Solo texto en Telegram para MVP.
- Escenarios formulados: entrevista consular (turista, estudiante, trabajo), entrevista laboral, due diligence con inversionista.
- Guardar transcripciones y resultados en base de datos para análisis posterior.

## 9. Pipeline Análisis de Negocios
1. Recibir documentos del cliente (estados financieros, contratos, licencias).
2. OCR + parsing.
3. IA identifica puntos críticos y solicita información faltante si aplica.
4. Integración con fuentes externas: criminalidad, noticias, demografía, tendencias del mercado local.
5. Generación de reporte integral (riesgos, fortalezas, recomendaciones).

## 10. Experiencia Telegram
- Comandos principales: `/start`, `/assessment`, `/roadmap`, `/checklist`, `/documentos`, `/simulacion`, `/ayuda`.
- Inline flows para solicitar datos específicos (ej. "sube documento", "ingresa empresa de interés").
- Notificaciones automáticas de fechas clave, recordatorios de tareas, actualizaciones legales relevantes.

## 11. Panel Administrativo (Web)
- Gestión de usuarios y estados de proceso.
- Vista de roadmap generado, comentarios, formularios en progreso.
- Control de scraping y fuentes (estado, última actualización, errores).
- Dashboards de métricas: conversiones, cumplimiento, fuentes consultadas.

## 12. Roadmap Futuro (Post-MVP)
- **Comunidad estilo red social**: espacio privado tipo “Facebook” para migrantes (posts, grupos, eventos, mentoring).
- **Marketplace integral**: productos y servicios ofrecidos por migrantes (emprendimientos, bienes raíces, alquileres, servicios profesionales, marketplace estilo MercadoLibre). Incluye ranking de confianza y reputación.
- **Audio/Video**: entrevistas simuladas con voz/video, webinars, lives.
- **Soporte multicanal**: web app completa, apps móviles, integraciones WhatsApp.
- **Automatización avanzada**: agentes especializados para cada ruta (visa trabajo, estudio, inversión) y workflows no-code para admins.

## 13. Próximos Pasos Inmediatos
1. Inventariar fuentes y crear fichas técnicas (responsables, permisos, scrape freq).
2. Diseñar arquitectura del pipeline RAG + almacenamiento (diagrama + especificación técnica).
3. Evaluar OCR con dataset controlado y documentar resultados.
4. Seleccionar modelo en Ollama y definir prompts base + herramientas.
5. Especificar flujo de formularios con revisión/firma (diagramas BPMN).
6. Definir estructura del panel admin (wireframes) y endpoints necesarios.
7. Configurar repositorio para almacenar conocimientos (vector store) y scripts de scraping.

---

**Nota final:** Este plan sirve como hoja de ruta técnica para implementar el MVP de MigPAL con enfoque en migración a EE. UU., preparando la base para futuras funcionalidades de comunidad y marketplace que convertirán la plataforma en un ecosistema integral para migrantes.
