# MigPAL Backend

## Pasos rápidos para iniciar Atlas + API
1. **Arranca el backend** (desde `backend/`):
   ```bash
   source .venv/bin/activate
   uvicorn app.api:app --host 0.0.0.0 --port 8000
   ```
2. **Arranca Ollama (GPU)**:
   ```bash
   ollama pull llama3.1:70b   # solo la primera vez
   OLLAMA_HOST=0.0.0.0:11434 ollama serve
   ```
3. **Habla con Atlas vía curl**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/ai/chat \
     -H "Authorization: Bearer <TU_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"question":"Hola Atlas, ¿qué requisitos necesito para una visa H-1B?","context":{}}'
   ```
4. **(Opcional) Simulación RAG**:
   ```bash
   OLLAMA_URL=http://localhost:11434 \
   AI_MODEL=llama3.1:70b \
   python scripts/bot_simulation.py "¿Qué documentos necesito para visa H-1B?"
   ```

## Componentes relevantes
- Scrapers (`/api/v1/data-sources` + `/jobs`) → USCIS, DOS, Zillow, BizBuySell, GreatSchools, LinkedIn Jobs.
- RAG → `GET /api/v1/knowledge/documents`.
- Planner → `/api/v1/planner`, `/api/v1/planner/sync` (script `backend/scripts/run_scheduler.py`).
- Bot helper → `/api/v1/bot/next-step`.
