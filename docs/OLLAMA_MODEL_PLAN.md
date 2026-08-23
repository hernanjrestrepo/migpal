# Plan de Selección y Configuración del Modelo IA (Ollama)

## Requisitos Funcionales
- Comprensión profunda de procesos migratorios, leyes, finanzas, vivienda, negocios.
- Soporte multilingüe (ES, EN, portugués, francés opcional).
- Razonamiento para análisis documental, formularios, scoring y simulaciones.
- Ventana de contexto amplia (>16K tokens ideal; 32K deseable).
- Soporte para tool-calling (invocar scraping, RAG, OCR, formularios, scoring).

## Candidatos Principales (Ollama)
1. **Llama 3 (70B o 8B finetuned)** – Buen balance de razonamiento y contexto; requiere hardware robusto.
2. **Mixtral 8x7B** – Modelo ensemble con buen rendimiento en razonamiento, requiere optimización en inferencia.
3. **Qwen2 (72B o 32B)** – Multi-idioma fuerte, buena precisión en tareas técnicas.
4. **Phi-3 Medium** – Más liviano, ideal para prototipos o recursos limitados.
5. **Mistral Large** – Capacidad similar a GPT-4 class (dependiendo disponibilidad en Ollama).

## Criterios de Evaluación
| Criterio | Peso |
|----------|------|
| Razonamiento jurídico/procedimental | 25% |
| Soporte multilingüe | 20% |
| Manejo de contexto largo | 15% |
| Rendimiento (latencia, recursos) | 15% |
| Integración con herramientas (tool calling) | 15% |
| Comunidad & actualizaciones | 10% |

## Metodología
1. **Benchmark interno** con prompts reales: asesorías legales, generación de formularios, análisis financiero, simulaciones.
2. **Pruebas multi-idioma** con textos mixtos y documentos.
3. **Evaluar tool-calling**: capacidad para estructurar llamadas a funciones de backend.
4. **Medir consumo de recursos** (CPU/GPU, RAM) y latencia por respuesta.
5. **Ponderar scores** según tabla y seleccionar modelo (o combinación) óptimo.

## Tooling con Ollama
- Definir conjunto de herramientas que IA puede invocar:
  - `rag_query`
  - `scrape_source`
  - `ocr_process`
  - `form_generate`
  - `probability_score`
  - `simulation_engine`
  - `doc_feedback`
- Implementar broker intermedio para validar inputs/outputs y registrar auditoría.

## Estrategia de Despliegue
- Ambiente de staging con hardware GPU dedicado para pruebas.
- Ajuste de parámetros (temperature, top_p, max_tokens) según uso (asistente, formularios, simulaciones).
- Fine-tuning o instrucción adicional usando dataset propio (documentación migratoria, guías, mejores prácticas) en fases posteriores.

## Roadmap
1. Ejecutar benchmark inicial con 2-3 modelos candidatos.
2. Seleccionar modelo principal y fallback.
3. Integrar tool-calling en backend.
4. Monitorear métricas (precisión, tiempo, feedback usuarios) para iterar.
