# Vista de Procesos - Modelo 4+1

## Descripción General

La Vista de Procesos describe los aspectos dinámicos del sistema: flujos de ejecución, procesos concurrentes, comunicación y sincronización entre componentes en tiempo de ejecución.

---

## Diagrama de Secuencia Principal

### Flujo: Consulta del Estudiante al Profesor Virtual

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Unity   │     │ Backend  │     │ Teacher  │     │ Medical  │     │ RAG      │     │  Ollama  │
│  Client  │     │  API     │     │ Service  │     │ Repo     │     │ Prompts  │     │  LLM     │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │                │
     │  POST /consultar_profesor       │                │                │                │
     │  {simulation_state}             │                │                │                │
     │───────────────▶│                │                │                │                │
     │                │                │                │                │                │
     │                │ get_educational_feedback()      │                │                │
     │                │───────────────▶│                │                │                │
     │                │                │                │                │                │
     │                │                │ _build_query() │                │                │
     │                │                │───────┐        │                │                │
     │                │                │       │ Extract tumor_diameter, stage,          │
     │                │                │◀──────┘ pack_years, treatment_efficacy          │
     │                │                │                │                │                │
     │                │                │ find_similar() │                │                │
     │                │                │───────────────▶│                │                │
     │                │                │                │                │                │
     │                │                │                │ ChromaDB.query()                │
     │                │                │                │───────┐        │                │
     │                │                │                │       │ Vector similarity       │
     │                │                │                │◀──────┘ search                  │
     │                │                │                │                │                │
     │                │                │ List[Document] │                │                │
     │                │                │◀───────────────│                │                │
     │                │                │                │                │                │
     │                │                │ _rerank_documents()             │                │
     │                │                │───────┐        │                │                │
     │                │                │       │ Cross-encoder scoring   │                │
     │                │                │◀──────┘                         │                │
     │                │                │                │                │                │
     │                │                │ build_educational_prompt()      │                │
     │                │                │────────────────────────────────▶│                │
     │                │                │                │                │                │
     │                │                │ prompt_string  │                │                │
     │                │                │◀───────────────────────────────│                │
     │                │                │                │                │                │
     │                │                │ llm_client.query()              │                │
     │                │                │───────────────────────────────────────────────▶│
     │                │                │                │                │                │
     │                │                │                │                │  HTTP POST     │
     │                │                │                │                │  /api/generate │
     │                │                │                │                │                │
     │                │                │ LLM response   │                │                │
     │                │                │◀──────────────────────────────────────────────│
     │                │                │                │                │                │
     │                │                │ _parse_response()               │                │
     │                │                │───────┐        │                │                │
     │                │                │       │ Extract JSON from response               │
     │                │                │◀──────┘                         │                │
     │                │                │                │                │                │
     │                │ TeacherResponse│                │                │                │
     │                │◀───────────────│                │                │                │
     │                │                │                │                │                │
     │  HTTP 200      │                │                │                │                │
     │  {teacher_response}             │                │                │                │
     │◀───────────────│                │                │                │                │
     │                │                │                │                │                │
     ▼                ▼                ▼                ▼                ▼                ▼
```

---

## Diagrama de Actividades: Pipeline RAG

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RAG Pipeline                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │     START       │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │ Build Query     │  Extract: stage, tumor_diameter, pack_years,          │
│  │ from State      │  treatments applied, current efficacy                 │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                               │
│  │ Generate Query  │────▶│   ChromaDB      │                               │
│  │ Embedding       │     │   Collection    │                               │
│  │ (BGE-M3)        │     │                 │                               │
│  └─────────────────┘     └────────┬────────┘                               │
│                                   │                                         │
│                                   ▼                                         │
│                          ┌─────────────────┐                               │
│                          │ Retrieve Top-K  │  K = 10 (config.RAG_TOP_K)   │
│                          │ Documents       │                               │
│                          └────────┬────────┘                               │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                     RERANKING PHASE                              │       │
│  ├─────────────────────────────────────────────────────────────────┤       │
│  │                                                                  │       │
│  │  ┌─────────────────┐                                            │       │
│  │  │ Cross-Encoder   │  Model: ms-marco-MiniLM-L-6-v2             │       │
│  │  │ Scoring         │                                            │       │
│  │  └────────┬────────┘                                            │       │
│  │           │                                                      │       │
│  │           ▼                                                      │       │
│  │  ┌─────────────────┐                                            │       │
│  │  │ Filter by       │  Threshold = 0.3                           │       │
│  │  │ Relevance Score │                                            │       │
│  │  └────────┬────────┘                                            │       │
│  │           │                                                      │       │
│  │           ▼                                                      │       │
│  │  ┌─────────────────┐                                            │       │
│  │  │ Sort by Score   │  Keep top-5 most relevant                  │       │
│  │  │ Descending      │                                            │       │
│  │  └─────────────────┘                                            │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────┐     ┌─────────────────┐                               │
│  │ Build Prompt    │◀────│ Context Docs    │                               │
│  │ with Context    │     │ (Grounding)     │                               │
│  └────────┬────────┘     └─────────────────┘                               │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │ LLM Generation  │  Ollama (llama3.2 / mistral)                          │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │ Parse JSON      │  Extract: explicacion, reflexion,                     │
│  │ Response        │  sugerencias, advertencia, confianza                  │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │      END        │  Return TeacherResponse                               │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Diagrama de Estado: Ciclo de Vida de la Simulación VR

```
                                    ┌───────────────────┐
                                    │                   │
                                    ▼                   │
┌──────────────┐     ┌──────────────────────┐         │
│              │     │                      │         │
│   IDLE       │────▶│   SELECTING_MODE     │         │
│              │     │                      │         │
└──────────────┘     └──────────┬───────────┘         │
       ▲                        │                      │
       │               ┌────────┴────────┐             │
       │               ▼                 ▼             │
       │     ┌─────────────────┐  ┌─────────────────┐ │
       │     │   FREE_MODE     │  │  LIBRARY_MODE   │ │
       │     │                 │  │                 │ │
       │     │ • Custom params │  │ • Load case    │ │
       │     │ • Any tumor size│  │ • Fixed params │ │
       │     │ • Exploration   │  │ • Validation   │ │
       │     └────────┬────────┘  └────────┬────────┘ │
       │              │                    │          │
       │              └────────┬───────────┘          │
       │                       ▼                      │
       │             ┌─────────────────┐              │
       │             │   SIMULATING    │              │
       │             │                 │              │
       │             │ • RK4 step loop │              │
       │             │ • Update tumor  │              │
       │             │ • Apply treatmt │              │
       │             └────────┬────────┘              │
       │                      │                       │
       │                      │ [time_step complete]  │
       │                      ▼                       │
       │             ┌─────────────────┐              │
       │             │   CONSULTING    │──────────────┘
       │             │   TEACHER       │  [retry/continue]
       │             │                 │
       │             │ • Send state    │
       │             │ • Wait response │
       │             │ • Show feedback │
       │             └────────┬────────┘
       │                      │
       │          ┌───────────┴───────────┐
       │          ▼                       ▼
       │  ┌─────────────────┐    ┌─────────────────┐
       │  │  SIMULATION_    │    │   EXAM_MODE     │
       │  │  COMPLETE       │    │                 │
       │  │                 │    │ • Timed session │
       │  │ • Show results  │    │ • Graded resp.  │
       │  │ • Compare cases │    │ • Professor see │
       │  └────────┬────────┘    └────────┬────────┘
       │           │                      │
       └───────────┴──────────────────────┘
                   [reset]
```

---

## Flujo de Comunicación HTTP

### Request/Response Típico

```
Unity VR Client                                Python Backend
      │                                              │
      │   HTTP POST /consultar_profesor              │
      │   Content-Type: application/json             │
      │   ─────────────────────────────────────────▶│
      │   {                                          │
      │     "tumor_diameter_cm": 2.5,                │
      │     "stage": "II",                           │
      │     "pack_years": 30.0,                      │
      │     "treatment_type": "chemotherapy",        │
      │     "treatment_efficacy": 65.0,              │
      │     "simulation_day": 45                     │
      │   }                                          │
      │                                              │
      │                     Processing...            │
      │                     (RAG + LLM: ~2-5 sec)    │
      │                                              │
      │   HTTP 200 OK                                │
      │   Content-Type: application/json             │
      │◀─────────────────────────────────────────────│
      │   {                                          │
      │     "explicacion": "El tumor en estadío II...",
      │     "reflexion": "¿Has considerado la...",   │
      │     "sugerencias": ["Evaluar QT adyuvante..."],
      │     "advertencia": null,                     │
      │     "confianza": 0.85,                       │
      │     "fuentes_utilizadas": ["Harrison...", ...]
      │   }                                          │
      │                                              │
      ▼                                              ▼
```

---

## Concurrencia y Paralelismo

### Modelo de Concurrencia del Backend

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI + Uvicorn                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                      Event Loop (asyncio)                          │    │
│   ├───────────────────────────────────────────────────────────────────┤    │
│   │                                                                    │    │
│   │    Request 1      Request 2      Request 3      Request N         │    │
│   │    (User A)       (User B)       (User C)       (User ...)        │    │
│   │        │              │              │              │              │    │
│   │        ▼              ▼              ▼              ▼              │    │
│   │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐         │    │
│   │   │ Handler │   │ Handler │   │ Handler │   │ Handler │         │    │
│   │   │ Corout. │   │ Corout. │   │ Corout. │   │ Corout. │         │    │
│   │   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘         │    │
│   │        │              │              │              │              │    │
│   │        └──────────────┴──────────────┴──────────────┘              │    │
│   │                              │                                      │    │
│   │                              ▼                                      │    │
│   │                    ┌─────────────────┐                             │    │
│   │                    │ Shared Resources │                            │    │
│   │                    │ • ChromaDB Client│ (thread-safe)              │    │
│   │                    │ • HTTP Pool      │ (for Ollama)               │    │
│   │                    │ • Embedding Model│ (loaded once)              │    │
│   │                    └─────────────────┘                             │    │
│   │                                                                    │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│   Workers: 1 (default uvicorn) - puede escalarse con gunicorn workers      │
│   I/O Bound: RAG queries, LLM calls son async (httpx)                      │
│   CPU Bound: Embedding generation (podría usar thread pool)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Puntos de Sincronización

| Recurso | Tipo | Estrategia |
|---------|------|------------|
| ChromaDB Collection | Compartido | Cliente thread-safe, singleton |
| Embedding Model | Compartido | Cargado al inicio, read-only |
| Ollama HTTP Client | Compartido | Connection pool (httpx) |
| Settings | Read-only | Cargado una vez al startup |

---

## Manejo de Errores y Timeouts

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐                                              │
│  │ HTTP Request  │                                              │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐     ┌───────────────┐                        │
│  │ Pydantic      │─NO─▶│ HTTP 422      │  Validation Error     │
│  │ Validation    │     │ Unprocessable │                        │
│  └───────┬───────┘     └───────────────┘                        │
│          │ OK                                                    │
│          ▼                                                       │
│  ┌───────────────┐     ┌───────────────┐                        │
│  │ ChromaDB      │─ERR▶│ HTTP 500      │  + Log + Fallback     │
│  │ Query         │     │ Internal Err  │  (empty context)      │
│  └───────┬───────┘     └───────────────┘                        │
│          │ OK                                                    │
│          ▼                                                       │
│  ┌───────────────┐     ┌───────────────┐                        │
│  │ Ollama LLM    │─ERR▶│ Mock Response │  Automatic fallback   │
│  │ Query         │     │ Generated     │  if Ollama unavailable│
│  └───────┬───────┘     └───────────────┘                        │
│          │ OK                                                    │
│          ▼                                                       │
│  ┌───────────────┐     ┌───────────────┐                        │
│  │ JSON Parse    │─ERR▶│ Default Resp  │  + Warning logged     │
│  │ Response      │     │ Structure     │                        │
│  └───────┬───────┘     └───────────────┘                        │
│          │ OK                                                    │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ HTTP 200 OK   │                                              │
│  └───────────────┘                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tiempos de Respuesta Esperados

| Fase | Tiempo Típico | Observaciones |
|------|---------------|---------------|
| Validación Pydantic | < 1ms | Sincrónico |
| ChromaDB Query | 50-200ms | Depende de colección |
| Embedding Generation | 100-500ms | GPU acelera |
| Cross-Encoder Rerank | 200-800ms | 10 docs típico |
| Ollama Generation | 2-10s | Depende del modelo |
| **Total E2E** | **3-12s** | Sin caché |

---

## Herramientas Recomendadas

- **PlantUML** o **Mermaid** para diagramas de secuencia
- **Draw.io** para diagramas de actividad
- Usar colores para distinguir actores/sistemas
