# Vista Lógica - Modelo 4+1

## Descripción General

La Vista Lógica describe la estructura estática del sistema mediante clases, interfaces y sus relaciones. PulmoMed es un sistema educativo de simulación de cáncer de pulmón con dos componentes principales: un **Backend Python** (IA + RAG) y un **Cliente Unity** (VR + Modelo Matemático).

---

## Diagrama de Clases Principal

### Instrucciones para el diagrama

Crear un **diagrama de clases UML** con los siguientes elementos:

---

### Paquete: `app.models` (Domain Models)

```
┌─────────────────────────────────────────┐
│           SimulationState               │
├─────────────────────────────────────────┤
│ - age: int                              │
│ - is_smoker: bool                       │
│ - pack_years: float                     │
│ - diet: Literal["saludable","normal","mala"] │
│ - sensitive_tumor_volume: float         │
│ - resistant_tumor_volume: float         │
│ - active_treatment: Literal[...]        │
│ - treatment_days: int                   │
│ - mode: Literal["libre","biblioteca"]   │
│ - case_id: str | None                   │
├─────────────────────────────────────────┤
│ + total_volume: float <<property>>      │
│ + approx_stage: str <<property>>        │
│ + compute_risk_score(): float           │
│ + update_lung_state(): LungState        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           TeacherResponse               │
├─────────────────────────────────────────┤
│ - explanation: str                      │
│ - recommendation: str                   │
│ - sources: list[str]                    │
│ - warning: str | None                   │
│ - retrieved_chunks: int                 │
│ - llm_model: str                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            LibraryCase                  │
├─────────────────────────────────────────┤
│ - case_id: str                          │
│ - title: str                            │
│ - description: str                      │
│ - age: int                              │
│ - is_smoker: bool                       │
│ - pack_years: float                     │
│ - diet: str                             │
│ - initial_sensitive_volume: float       │
│ - initial_resistant_volume: float       │
│ - learning_objectives: list[str]        │
│ - statistical_source: str               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│             LungState                   │
├─────────────────────────────────────────┤
│ <<enumeration>>                         │
│ SANO                                    │
│ EN_RIESGO                               │
│ ESTABLE                                 │
│ PROGRESANDO                             │
│ CRITICO                                 │
│ TERMINAL                                │
└─────────────────────────────────────────┘
```

**Relaciones:**
- `SimulationState` **usa** `LungState` (composición)
- `LibraryCase` puede **generar** `SimulationState` (dependencia)

---

### Paquete: `app.services` (Business Logic)

```
┌─────────────────────────────────────────┐
│          AITeacherService               │
├─────────────────────────────────────────┤
│ - settings: Settings                    │
│ - repository: MedicalKnowledgeRepository│
│ - llm_client: LLMClient                 │
│ - prompt_templates: PromptTemplates     │
├─────────────────────────────────────────┤
│ + get_educational_feedback(state): TeacherResponse │
│ - _build_search_query(state): str       │
│ - _filter_and_rerank_chunks(): list     │
│ - _parse_llm_response(): TeacherResponse│
│ - _is_malicious(text): bool             │
└─────────────────────────────────────────┘
```

**Relaciones:**
- `AITeacherService` **depende de** `MedicalKnowledgeRepository` (inyección)
- `AITeacherService` **depende de** `LLMClient` (inyección)
- `AITeacherService` **usa** `PromptTemplates` (composición)
- `AITeacherService` **recibe** `SimulationState` y **retorna** `TeacherResponse`

---

### Paquete: `app.repositories` (Data Access)

```
┌─────────────────────────────────────────┐
│      MedicalKnowledgeRepository         │
├─────────────────────────────────────────┤
│ - settings: Settings                    │
│ - _client: ChromaDB.PersistentClient    │
│ - _collection: Collection               │
│ - _embedding_model: SentenceTransformer │
├─────────────────────────────────────────┤
│ + initialize(): void                    │
│ + retrieve_relevant_chunks(query, top_k): list[dict] │
│ + add_documents(texts, metadatas): void │
│ + get_collection_stats(): dict          │
│ + close(): void                         │
└─────────────────────────────────────────┘

<<singleton>>
get_repository() → MedicalKnowledgeRepository
```

**Relaciones:**
- `MedicalKnowledgeRepository` **usa** `ChromaDB` (agregación externa)
- `MedicalKnowledgeRepository` **usa** `SentenceTransformer` (BGE-M3)

---

### Paquete: `app.llm` (LLM Abstraction)

```
┌─────────────────────────────────────────┐
│         <<interface>>                   │
│           LLMClient                     │
├─────────────────────────────────────────┤
│ + query(prompt: str): str               │
│ + check_availability(): bool            │
└─────────────────────────────────────────┘
            △
            │ implementa
    ┌───────┴───────┐
    │               │
┌───┴───┐     ┌─────┴─────┐
│OllamaClient│  │  MockLLM  │
├───────────┤  ├───────────┤
│-settings  │  │-responses │
│-_force_mock│ │-call_count│
├───────────┤  ├───────────┤
│+query()   │  │+query()   │
│+check_availability()│    │
│-_mock_response()│        │
│-_ollama_query() │        │
└───────────┘  └───────────┘
```

**Relaciones:**
- `OllamaClient` y `MockLLM` **implementan** `LLMClient` (Protocol)
- `OllamaClient` puede usar **Ollama Server** via HTTP o fallback a mock

---

### Paquete: `app.rag` (RAG Components)

```
┌─────────────────────────────────────────┐
│          PromptTemplates                │
├─────────────────────────────────────────┤
│ + SYSTEM_PROMPT: str <<class>>          │
│ + TEACHER_QUERY_TEMPLATE: str <<class>> │
│ + PROGRESSION_ANALYSIS_TEMPLATE: str    │
│ + TREATMENT_RESPONSE_TEMPLATE: str      │
├─────────────────────────────────────────┤
│ + format_context(chunks): str <<static>>│
│ + build_teacher_prompt(state, chunks): str │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          MedicalPDFLoader               │
├─────────────────────────────────────────┤
│ - settings: Settings                    │
│ - repository: MedicalKnowledgeRepository│
├─────────────────────────────────────────┤
│ + load_pdf(path): list[dict]            │
│ + load_directory(path): list[dict]      │
│ + index_chunks(chunks): void            │
└─────────────────────────────────────────┘
```

---

### Paquete Unity: `LungCancerVR.MathModel` (C#)

```
┌─────────────────────────────────────────┐
│         TumorGrowthModel                │
├─────────────────────────────────────────┤
│ - SensitiveCells: float                 │
│ - ResistantCells: float                 │
│ - K: float (capacidad de carga)         │
│ - rs_base, rr_base: float               │
│ - patient: PatientProfile               │
│ - treatment: ITreatmentStrategy         │
│ - solver: RK4Solver                     │
├─────────────────────────────────────────┤
│ + TotalVolume: float <<property>>       │
│ + Simulate(days): void                  │
│ + SetTreatment(strategy): void          │
│ - ComputeDerivatives(): float[]         │
│ - GetAdjustedRs(): float                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          PatientProfile                 │
├─────────────────────────────────────────┤
│ - Age: int                              │
│ - IsSmoker: bool                        │
│ - PackYears: float                      │
│ - Diet: DietType                        │
│ - GeneticFactor: float                  │
├─────────────────────────────────────────┤
│ + GetAgeGrowthModifier(): float         │
│ + GetSmokingCapacityModifier(): float   │
│ + GetDietModifier(): float              │
│ + IsValid(out error): bool              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     <<interface>>                       │
│     ITreatmentStrategy                  │
├─────────────────────────────────────────┤
│ + GetBeta(timeSinceTreatment): float    │
│ + TreatmentName: string                 │
└─────────────────────────────────────────┘
            △
            │ implementa
    ┌───────┼───────┬───────┐
    │       │       │       │
┌───┴───┐ ┌─┴─┐  ┌──┴──┐ ┌──┴──┐
│NoTreatment│Chemo│Radio│Immuno│
└───────┘ └───┘  └─────┘ └─────┘

┌─────────────────────────────────────────┐
│            RK4Solver                    │
├─────────────────────────────────────────┤
│ - stepSize: float                       │
│ - derivatives: Func<float,float[],float[]> │
├─────────────────────────────────────────┤
│ + Solve(t0, y0, tEnd): float[]          │
│ + Step(t, y): float[]                   │
└─────────────────────────────────────────┘
```

**Relaciones:**
- `TumorGrowthModel` **tiene** `PatientProfile` (composición)
- `TumorGrowthModel` **tiene** `ITreatmentStrategy` (agregación)
- `TumorGrowthModel` **usa** `RK4Solver` (composición)
- Tratamientos concretos **implementan** `ITreatmentStrategy`

---

## Diagrama de Paquetes

```
┌─────────────────────────────────────────────────────────────┐
│                    PulmoMed System                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │   Unity VR Client    │    │   Python Backend     │      │
│  │   (C#)               │    │   (FastAPI)          │      │
│  ├──────────────────────┤    ├──────────────────────┤      │
│  │ ┌──────────────────┐ │    │ ┌──────────────────┐ │      │
│  │ │ LungCancerVR.    │ │    │ │    app.api       │ │      │
│  │ │ MathModel        │ │    │ │ (REST Endpoints) │ │      │
│  │ └────────┬─────────┘ │    │ └────────┬─────────┘ │      │
│  │          │           │    │          │           │      │
│  │ ┌────────▼─────────┐ │    │ ┌────────▼─────────┐ │      │
│  │ │ UnityEngine      │ │    │ │  app.services    │ │      │
│  │ │ (VR Rendering)   │ │◄──HTTP──►(AITeacher)   │ │      │
│  │ └──────────────────┘ │    │ └────────┬─────────┘ │      │
│  │                      │    │          │           │      │
│  └──────────────────────┘    │ ┌────────▼─────────┐ │      │
│                              │ │ app.repositories │ │      │
│                              │ │ (ChromaDB)       │ │      │
│                              │ └────────┬─────────┘ │      │
│                              │          │           │      │
│                              │ ┌────────▼─────────┐ │      │
│                              │ │    app.llm       │ │      │
│                              │ │ (Ollama/Mock)    │ │      │
│                              │ └──────────────────┘ │      │
│                              └──────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Notas de Implementación

| Patrón | Uso en el Sistema |
|--------|-------------------|
| **Repository Pattern** | `MedicalKnowledgeRepository` abstrae ChromaDB |
| **Strategy Pattern** | `ITreatmentStrategy` para diferentes tratamientos |
| **Dependency Injection** | `AITeacherService` recibe repository y llm_client |
| **Singleton** | `get_repository()` y `get_settings()` |
| **Protocol (Interface)** | `LLMClient` define contrato para LLMs |
| **Factory** | `get_repository()` como factory function |

---

## Herramienta Recomendada

- **PlantUML** o **Mermaid** para generar diagramas
- Exportar en formato PNG/SVG para documentación
