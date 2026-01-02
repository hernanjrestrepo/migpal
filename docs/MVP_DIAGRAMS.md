# MigPAL MVP – Diagramas Técnicos

## 1. Diagrama de Contenedores (C4 N3)
```mermaid
graph TD
    subgraph Client Layer
        TG[Usuario en Telegram]
        Admin[Administrador Web]
    end

    subgraph Backend Layer
        BOT[Servicio Bot Telegram]
        API[Backend Orquestador FastAPI]
        IA[Motor IA (Ollama + Tools)]
        SCR[Workers Scraping / RAG]
        OCR[Servicio OCR]
        FORM[Generador Formularios & Firma]
        SCORE[Motor Probabilidad]
        SIM[Motor Simulaciones]
        PANEL[Frontend Admin]
    end

    subgraph Data Layer
        DB[(PostgreSQL)]
        VEC[(Vector Store)]
        FILES[(Almacenamiento S3-Compatible)]
        LOGS[(Observabilidad)]
    end

    TG <--> BOT
    BOT <--> API
    Admin <--> PANEL
    PANEL <--> API

    API --> IA
    API --> OCR
    API --> FORM
    API --> SCORE
    API --> SIM

    IA --> VEC
    SCR --> VEC
    SCR --> DB

    API --> DB
    API --> FILES
    OCR --> FILES
    FORM --> FILES

    API --> LOGS
    SCR --> LOGS
    BOT --> LOGS
```

## 2. Flujo de Interacción en Telegram
```mermaid
sequenceDiagram
    participant U as Usuario
    participant TG as Bot Telegram
    participant API as Backend
    participant IA as Motor IA
    participant DB as Base de Datos

    U->>TG: /assessment
    TG->>API: Solicitud assessment
    API->>DB: Guardar/recuperar respuestas
    API->>IA: Generar resumen + roadmap
    IA->>API: Roadmap + recomendaciones
    API->>DB: Persistir roadmap
    API->>TG: Respuesta al usuario

    U->>TG: Sube documento
    TG->>API: Notifica archivo
    API->>OCR: Procesar documento
    OCR->>API: Resultado estructurado
    API->>IA: Validar requisitos / detectar faltantes
    IA->>API: Feedback
    API->>TG: Informe al usuario
```

## 3. Flujo BPMN (Generación y Firma de Formularios)
```mermaid
flowchart TD
    A[Inicia solicitud de formulario] --> B{Información completa?}
    B -- No --> C[Solicitar datos faltantes vía Telegram]
    C --> B
    B -- Sí --> D[Generar borrador con IA]
    D --> E[Enviar borrador al usuario]
    E --> F{Cliente aprueba?}
    F -- No --> G[Recibir observaciones]
    G --> H[IA ajusta documento]
    H --> E
    F -- Sí --> I{¿Requiere firma electrónica?}
    I -- Sí --> J[Enviar a servicio de firma]
    J --> K[Documento firmado]
    I -- No --> K
    K --> L[Guardar versión final en repositorio]
    L --> M[Actualizar checklist y roadmap]
```

## 4. Flujo de Actualización de Conocimiento (Scraping + RAG)
```mermaid
flowchart LR
    Start[Scheduler] --> Discover[Selecciona fuente]
    Discover --> Scrape[Ejecuta scraper/API]
    Scrape --> Clean[Normaliza y limpia datos]
    Clean --> Chunk[Segmenta en chunks]
    Chunk --> Embed[Calcula embeddings]
    Embed --> Store[Actualiza Vector Store]
    Clean --> Meta[Actualiza metadatos en DB]
    Store --> Notify[Notifica motor IA de nueva versión]
    Notify --> End[Disponible para consultas]
```
```
