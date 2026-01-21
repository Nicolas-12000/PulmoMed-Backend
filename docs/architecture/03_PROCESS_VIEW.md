# Vista de Procesos - Modelo 4+1 de Kruchten

> **Propósito**: Describir los aspectos dinámicos del sistema: flujos de ejecución, procesos concurrentes, comunicación entre componentes y comportamiento en tiempo de ejecución.
>
> **Audiencia**: Integradores de sistemas, Desarrolladores, DevOps.
>
> **Diagramas UML**: Diagrama de Secuencia, Diagrama de Actividad, Diagrama de Comunicación.

---

## 1. Introducción

La Vista de Procesos aborda la concurrencia, distribución, rendimiento y escalabilidad del sistema. En PulmoMed:

- **Backend**: Servidor async (FastAPI/Uvicorn) con event loop único
- **Cliente VR**: Game loop de Unity con comunicación HTTP no bloqueante
- **Comunicación**: REST/JSON sobre HTTP/1.1

Esta vista responde a la pregunta: *"¿Cómo se comporta el sistema en tiempo de ejecución?"*

---

## 2. Diagrama de Secuencia - Consulta al Profesor Virtual

Este es el **flujo principal** del sistema, representando el caso de uso más importante: el estudiante consulta al asistente IA durante una simulación.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIAGRAMA DE SECUENCIA UML - CONSULTA AL PROFESOR                         │
│                                      (Escenario Principal)                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────┐      ┌──────────┐      ┌──────────────┐      ┌───────────┐      ┌─────────┐      ┌────────┐
  │ Usuario │      │  Unity   │      │   FastAPI    │      │ AITeacher │      │   RAG   │      │ Ollama │
  │(Quest 3)│      │ Client   │      │  Endpoint    │      │  Service  │      │ Engine  │      │  LLM   │
  └────┬────┘      └────┬─────┘      └──────┬───────┘      └─────┬─────┘      └────┬────┘      └───┬────┘
       │                │                   │                    │                 │               │
       │  1. Presiona   │                   │                    │                 │               │
       │  "Consultar"   │                   │                    │                 │               │
       │───────────────▶│                   │                    │                 │               │
       │                │                   │                    │                 │               │
       │                │  2. Serializa     │                    │                 │               │
       │                │  SimulationState  │                    │                 │               │
       │                │──────┐            │                    │                 │               │
       │                │◀─────┘            │                    │                 │               │
       │                │                   │                    │                 │               │
       │                │  3. POST /api/v1/consultar_profesor    │                 │               │
       │                │   {JSON payload}  │                    │                 │               │
       │                │──────────────────▶│                    │                 │               │
       │                │                   │                    │                 │               │
       │                │                   │  4. Validar con    │                 │               │
       │                │                   │     Pydantic       │                 │               │
       │                │                   │──────┐             │                 │               │
       │                │                   │◀─────┘             │                 │               │
       │                │                   │                    │                 │               │
       │                │                   │  5. get_educational_feedback(state)  │               │
       │                │                   │───────────────────▶│                 │               │
       │                │                   │                    │                 │               │
       │                │                   │                    │  6. check_cache()               │
       │                │                   │                    │──────┐          │               │
       │                │                   │                    │◀─────┘          │               │
       │                │                   │                    │                 │               │
       │                │                   │                    │      ┌──────────┴──────────┐    │
       │                │                   │                    │      │  alt [CACHE MISS]   │    │
       │                │                   │                    │      └──────────┬──────────┘    │
       │                │                   │                    │                 │               │
       │                │                   │                    │  7. _build_search_query(state)  │
       │                │                   │                    │──────┐          │               │
       │                │                   │                    │◀─────┘          │               │
       │                │                   │                    │                 │               │
       │                │                   │                    │  8. retrieve_relevant_chunks(q) │
       │                │                   │                    │────────────────▶│               │
       │                │                   │                    │                 │               │
       │                │                   │                    │                 │  9. embed(q)  │
       │                │                   │                    │                 │──────┐        │
       │                │                   │                    │                 │◀─────┘ BGE-M3 │
       │                │                   │                    │                 │               │
       │                │                   │                    │                 │ 10. vector    │
       │                │                   │                    │                 │     search    │
       │                │                   │                    │                 │──────┐        │
       │                │                   │                    │                 │◀─────┘ChromaDB│
       │                │                   │                    │                 │               │
       │                │                   │                    │  11. documents[]│               │
       │                │                   │                    │◀────────────────│               │
       │                │                   │                    │                 │               │
       │                │                   │                    │ 12. filter_and_rerank(docs)     │
       │                │                   │                    │──────┐          │               │
       │                │                   │                    │◀─────┘          │               │
       │                │                   │                    │                 │               │
       │                │                   │                    │ 13. build_prompt(state, docs)   │
       │                │                   │                    │──────┐          │               │
       │                │                   │                    │◀─────┘          │               │
       │                │                   │                    │                 │               │
       │                │                   │                    │ 14. query(prompt)               │
       │                │                   │                    │────────────────────────────────▶│
       │                │                   │                    │                 │               │
       │                │                   │                    │                 │    ┌──────────┤
       │                │                   │                    │                 │    │ 15. LLM  │
       │                │                   │                    │                 │    │ generate │
       │                │                   │                    │                 │    │ (3-10s)  │
       │                │                   │                    │                 │    └──────────┤
       │                │                   │                    │                 │               │
       │                │                   │                    │ 16. llm_response│               │
       │                │                   │                    │◀────────────────────────────────│
       │                │                   │                    │                 │               │
       │                │                   │                    │ 17. parse_response()            │
       │                │                   │                    │──────┐          │               │
       │                │                   │                    │◀─────┘          │               │
       │                │                   │                    │                 │               │
       │                │                   │                    │ 18. cache_response()            │
       │                │                   │                    │──────┐          │               │
       │                │                   │                    │◀─────┘          │               │
       │                │                   │                    │      └──────────┬──────────┘    │
       │                │                   │                    │                 │               │
       │                │                   │  19. TeacherResponse                 │               │
       │                │                   │◀───────────────────│                 │               │
       │                │                   │                    │                 │               │
       │                │  20. HTTP 200 OK  │                    │                 │               │
       │                │  {JSON response}  │                    │                 │               │
       │                │◀──────────────────│                    │                 │               │
       │                │                   │                    │                 │               │
       │                │ 21. Mostrar en    │                    │                 │               │
       │                │     panel 3D      │                    │                 │               │
       │                │──────┐            │                    │                 │               │
       │                │◀─────┘            │                    │                 │               │
       │                │                   │                    │                 │               │
       │ 22. Lee        │                   │                    │                 │               │
       │ explicación    │                   │                    │                 │               │
       │◀───────────────│                   │                    │                 │               │
       │                │                   │                    │                 │               │
       ▼                ▼                   ▼                    ▼                 ▼               ▼
```

---

## 3. Diagrama de Secuencia - Autenticación de Usuario

Basado en las imágenes de referencia proporcionadas, este diagrama modela el flujo de registro e inicio de sesión.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIAGRAMA DE SECUENCIA UML - AUTENTICACIÓN                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                                          ╔═══════════════════════════╗
                                          ║         REGISTRO          ║
                                          ╚═══════════════════════════╝

  ┌─────────┐           ┌────────┐           ┌───────────────────┐           ┌────────────┐
  │ Usuario │           │  Web   │           │ SistemaAutenticac.│           │BaseDeDatos │
  └────┬────┘           └───┬────┘           └─────────┬─────────┘           └──────┬─────┘
       │                    │                          │                            │
       │  1. Llenar form.   │                          │                            │
       │    de registro     │                          │                            │
       │───────────────────▶│                          │                            │
       │                    │                          │                            │
       │                    │  2. Solicitud registro   │                            │
       │                    │      (datos)             │                            │
       │                    │─────────────────────────▶│                            │
       │                    │                          │                            │
       │                    │                          │  3. Solicita asignación    │
       │                    │                          │     de rol                 │
       │                    │                          │───────────────────────────▶│
       │                    │                          │                            │
       │                    │                          │  4. Retorna rol            │
       │                    │                          │◀───────────────────────────│
       │                    │                          │                            │
       │                    │                          │  5. Guardar nuevo usuario  │
       │                    │                          │     y rol                  │
       │                    │                          │───────────────────────────▶│
       │                    │                          │                            │
       │                    │                          │  6. Confirmación           │
       │                    │                          │◀───────────────────────────│
       │                    │                          │                            │
       │                    │  7. Registro exitoso     │                            │
       │                    │◀─────────────────────────│                            │
       │                    │                          │                            │
       │  8. Mostrar        │                          │                            │
       │  mensaje éxito     │                          │                            │
       │◀───────────────────│                          │                            │
       │                    │                          │                            │

                                          ╔═══════════════════════════╗
                                          ║      INICIO SESIÓN        ║
                                          ╚═══════════════════════════╝

       │                    │                          │                            │
       │  9. Ingresar       │                          │                            │
       │  credenciales      │                          │                            │
       │───────────────────▶│                          │                            │
       │                    │                          │                            │
       │                    │ 10. Solicitud            │                            │
       │                    │     autenticación        │                            │
       │                    │─────────────────────────▶│                            │
       │                    │                          │                            │
       │                    │                          │ 11. Verificar              │
       │                    │                          │     credenciales           │
       │                    │                          │───────────────────────────▶│
       │                    │                          │                            │
       │                    │                          │ 12. Confirmación           │
       │                    │                          │◀───────────────────────────│
       │                    │                          │                            │
       │                    │ 13. Autenticación        │                            │
       │                    │     exitosa              │                            │
       │                    │◀─────────────────────────│                            │
       │                    │                          │                            │
       │ 14. Redirige       │                          │                            │
       │     según rol      │                          │                            │
       │◀───────────────────│                          │                            │
       │                    │                          │                            │
       ▼                    ▼                          ▼                            ▼
```

---

## 4. Diagrama de Actividad - Pipeline RAG

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           DIAGRAMA DE ACTIVIDAD UML - PIPELINE RAG                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                                         ●
                                         │
                                         ▼
                          ┌──────────────────────────────┐
                          │ 1. Recibir SimulationState   │
                          │    desde Cliente VR          │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────┐
                          │ 2. Validar con Pydantic      │
                          │    • Rangos de edad (18-100) │
                          │    • Volúmenes ≥ 0           │
                          │    • pack_years si fumador   │
                          └──────────────┬───────────────┘
                                         │
                              ┌──────────◇──────────┐
                              │                     │
                              ▼                     ▼
                         [Válido]              [Inválido]
                              │                     │
                              │                     ▼
                              │          ┌──────────────────────┐
                              │          │ Retornar HTTP 422    │
                              │          │ Validation Error     │
                              │          └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────────────┐
                   │ 3. Verificar Cache           │
                   │    key = hash(stage,         │
                   │    treatment, pack_bucket)   │
                   └──────────────┬───────────────┘
                                  │
                       ┌──────────◇──────────┐
                       │                     │
                       ▼                     ▼
                  [CACHE HIT]           [CACHE MISS]
                       │                     │
                       │                     ▼
                       │       ┌──────────────────────────────┐
                       │       │ 4. Construir Search Query    │
                       │       │    "Tumor estadío {stage},   │
                       │       │     tratamiento {treatment}" │
                       │       └──────────────┬───────────────┘
                       │                      │
                       │                      ▼
                       │       ┌──────────────────────────────┐
                       │       │ 5. Generar Embedding         │
                       │       │    BGE-M3 (multilingual)     │
                       │       │    → vector 1024 dims        │
                       │       └──────────────┬───────────────┘
                       │                      │
                       │                      ▼
                       │       ┌──────────────────────────────┐
                       │       │ 6. Vector Search ChromaDB    │
                       │       │    Cosine similarity         │
                       │       │    Top-K = 10 documentos     │
                       │       └──────────────┬───────────────┘
                       │                      │
                       │                      ▼
                       │       ┌──────────────────────────────┐
                       │       │ 7. Re-ranking                │
                       │       │    • Filtrar score < 0.3     │
                       │       │    • Ordenar por relevancia  │
                       │       │    • Mantener Top-5          │
                       │       └──────────────┬───────────────┘
                       │                      │
                       │                      ▼
                       │       ┌──────────────────────────────┐
                       │       │ 8. Construir Prompt          │
                       │       │    system_prompt +           │
                       │       │    context_docs +            │
                       │       │    simulation_state +        │
                       │       │    instrucciones educativas  │
                       │       └──────────────┬───────────────┘
                       │                      │
                       │                      ▼
                       │       ┌──────────────────────────────┐
                       │       │ 9. LLM Generation            │
                       │       │    Ollama (llama3.2)         │
                       │       │    Timeout: 15 segundos      │
                       │       └──────────────┬───────────────┘
                       │                      │
                       │           ┌──────────◇──────────┐
                       │           │                     │
                       │           ▼                     ▼
                       │     [Respuesta OK]        [Timeout/Error]
                       │           │                     │
                       │           │                     ▼
                       │           │       ┌──────────────────────┐
                       │           │       │ Fallback Response    │
                       │           │       │ "Sistema procesando" │
                       │           │       └──────────┬───────────┘
                       │           │                  │
                       │           ▼                  │
                       │   ┌──────────────────────────────┐
                       │   │ 10. Parsear Respuesta        │◀┘
                       │   │     Extraer JSON estructurado│
                       │   └──────────────┬───────────────┘
                       │                  │
                       │                  ▼
                       │   ┌──────────────────────────────┐
                       │   │ 11. Guardar en Cache         │
                       │   │     TTL = 5 minutos          │
                       │   └──────────────┬───────────────┘
                       │                  │
                       └─────────────────▶│
                                          ▼
                          ┌──────────────────────────────┐
                          │ 12. Retornar TeacherResponse │
                          │     + processing_time_ms     │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                                         ◉
```

---

## 5. Modelo de Concurrencia

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MODELO DE CONCURRENCIA                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI + Uvicorn (ASGI Server)                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              Event Loop (asyncio)                                        │   │
│   │                              Single-threaded, non-blocking                               │   │
│   ├─────────────────────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                                          │   │
│   │    Request 1          Request 2          Request 3          Request N                   │   │
│   │    (Quest A)          (Quest B)          (Quest C)          (...)                       │   │
│   │        │                  │                  │                  │                        │   │
│   │        ▼                  ▼                  ▼                  ▼                        │   │
│   │   ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐                 │   │
│   │   │ Coroutine│       │ Coroutine│       │ Coroutine│       │ Coroutine│                 │   │
│   │   │ Handler  │       │ Handler  │       │ Handler  │       │ Handler  │                 │   │
│   │   └─────┬────┘       └─────┬────┘       └─────┬────┘       └─────┬────┘                 │   │
│   │         │                  │                  │                  │                        │   │
│   │         └──────────────────┴──────────────────┴──────────────────┘                        │   │
│   │                                        │                                                  │   │
│   │                          await (I/O bound, no bloquea)                                   │   │
│   │                                        │                                                  │   │
│   │                                        ▼                                                  │   │
│   │         ╔═════════════════════════════════════════════════════════════════╗              │   │
│   │         ║                    RECURSOS COMPARTIDOS                          ║              │   │
│   │         ╠═════════════════════════════════════════════════════════════════╣              │   │
│   │         ║  • ChromaDB Client      → Singleton, thread-safe                 ║              │   │
│   │         ║  • Embedding Model      → Loaded once at startup (read-only)     ║              │   │
│   │         ║  • HTTP Connection Pool → httpx.AsyncClient (Ollama)             ║              │   │
│   │         ║  • Response Cache       → Dict con TTL (asyncio-safe)            ║              │   │
│   │         ║  • Settings             → Inmutable (Pydantic BaseSettings)      ║              │   │
│   │         ╚═════════════════════════════════════════════════════════════════╝              │   │
│   │                                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                  │
│   Configuración de Producción:                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │  • Workers: 1 (uvicorn default) — escalable con gunicorn a N workers                    │   │
│   │  • I/O Bound: RAG queries, LLM calls son async (no bloquean event loop)                 │   │
│   │  • CPU Bound: Embedding generation (puede usar ThreadPoolExecutor)                      │   │
│   │  • Max Connections: ~100 concurrent (httpx pool)                                        │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Tiempos de Respuesta por Fase

| Fase | Tiempo Típico | Tiempo Máximo | Categoría |
|------|---------------|---------------|-----------|
| Validación Pydantic | < 1 ms | 5 ms | Sync, CPU |
| Check Cache | < 1 ms | 2 ms | Sync, Memory |
| Build Query | < 5 ms | 10 ms | Sync, CPU |
| **Generate Embedding** | 100-300 ms | 500 ms | Sync, GPU/CPU |
| ChromaDB Query | 50-150 ms | 200 ms | Async, I/O |
| Reranking | 200-500 ms | 800 ms | Sync, CPU |
| **LLM Generation** | **2-8 s** | **15 s** | Async, I/O |
| Parse Response | < 10 ms | 50 ms | Sync, CPU |
| **Total E2E (sin cache)** | **3-10 s** | **15 s** | - |
| **Total E2E (cache hit)** | **< 50 ms** | **100 ms** | - |

---

## 7. Manejo de Errores y Fallbacks

| Punto de Fallo | Detección | Estrategia de Recuperación | Respuesta |
|----------------|-----------|---------------------------|-----------|
| Validación Pydantic | `ValidationError` | Mensaje de error detallado | HTTP 422 |
| ChromaDB no disponible | `ConnectionError` | Continuar sin contexto RAG | HTTP 200 (degradado) |
| Ollama timeout (>15s) | `asyncio.TimeoutError` | Respuesta educativa genérica | HTTP 200 (fallback) |
| Ollama no disponible | `ConnectionError` | Activar MockLLM | HTTP 200 (mock) |
| JSON parse error | `JSONDecodeError` | Respuesta por defecto | HTTP 200 (default) |
| Cache lleno (>100) | Verificación size | LRU eviction | N/A (interno) |
| Prompt injection | `_is_malicious()` | Rechazar consulta | HTTP 400 |

---

*Documento generado siguiendo el estándar 4+1 de Kruchten (IEEE Software, 1995)*
