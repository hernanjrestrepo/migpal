# Plan de Evaluación OCR – MigPAL

## Objetivo
Seleccionar la solución OCR óptima (o combinación) para procesar documentos migratorios multi-idioma con alta precisión, soportando formularios estructurados y reduciendo fricción para el usuario.

## Documentos a Procesar
- Formularios USCIS (PDF, escaneados).
- Pasaportes, IDs, actas (diversos países/idiomas).
- Estados financieros, contratos, facturas.
- Comprobantes de domicilio, cartas bancarias.

## Candidatos a Evaluar
1. **Tesseract** (open source, local)
2. **PaddleOCR** (open source, local)
3. **AWS Textract** (cloud)
4. **Google Document AI** (cloud)
5. **Azure Form Recognizer** (cloud)
6. (Opcional) **ABBYY FlexiCapture** (enterprise)

## Criterios y Pesos
| Criterio | Peso |
|----------|------|
| Precisión multi-idioma | 30% |
| Manejo de formularios/tablas | 20% |
| Latencia / Rendimiento | 15% |
| Costo total (CAPEX/OPEX) | 15% |
| Facilidad de integración (API/SDK) | 10% |
| Comunidad/Soporte | 10% |

## Dataset de Prueba
- Colección de ~200 documentos representativos (diversos idiomas, calidades de escaneo, formularios con campos). Se anonimizarán datos sensibles.
- Etiquetado manual de ground truth para medir exactitud (WER, posición de campos).

## Metodología
1. Preparar scripts para enviar documentos a cada servicio.
2. Medir métricas:
   - WER (Word Error Rate) promedio por idioma.
   - Exactitud en campos clave (nombre, fechas, números de documento).
   - Latencia promedio por documento.
   - Costos por lote (estimación mensual).
3. Puntuar cada candidato según pesos definidos.
4. Seleccionar el stack recomendado:
   - Opción base on-prem (p.ej. PaddleOCR) para volumen estándar.
   - Opción premium (Textract/Document AI) para casos complejos o bajo demanda.

## Entregables
- Matriz comparativa con scores.
- Decisión justificada del stack OCR.
- Recomendaciones de implementación e integración con backend (API endpoints, colas, almacenamiento temporal).
