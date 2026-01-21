# Vista Lógica - Modelo 4+1 de Kruchten

> **Propósito**: Describir la funcionalidad del sistema desde la perspectiva del usuario final, mostrando la estructura estática mediante clases, interfaces y sus relaciones.
>
> **Audiencia**: Usuarios finales, Diseñadores de sistemas, Arquitectos de software.
>
> **Diagramas UML**: Diagrama de Clases, Diagrama de Estados.

---

## 1. Introducción

La Vista Lógica descompone el sistema en abstracciones clave que representan los conceptos del dominio. En PulmoMed, el dominio se divide en dos subsistemas complementarios:

| Subsistema | Responsabilidad | Tecnología |
|------------|-----------------|------------|
| **Backend Python** | Asistente educativo con RAG + LLM | FastAPI, ChromaDB, Ollama |
| **Cliente Unity C#** | Simulación matemática y visualización VR | Unity, C# MathModel |

Esta vista responde a la pregunta: *"¿Qué hace el sistema y cómo está estructurado lógicamente?"*

---

## 2. Diagrama de Clases - Backend Python

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DIAGRAMA DE CLASES UML                                        │
│                                    Subsistema: Backend Python                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                   <<package>> app.models                                     ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌────────────────────────────────────┐
    │    <<enumeration>> LungState       │
    ├────────────────────────────────────┤
    │  SANO                              │
    │  EN_RIESGO                         │
    │  ESTABLE                           │
    │  PROGRESANDO                       │
    │  CRITICO                           │
    │  TERMINAL                          │
    └─────────────────┬──────────────────┘
                      │ <<uses>>
                      ▼
    ┌────────────────────────────────────────────────────────────────────────────────────────┐
    │                                   SimulationState                                       │
    │                                   <<entity>>                                            │
    ├────────────────────────────────────────────────────────────────────────────────────────┤
    │  - age: int {18..100}                                                                  │
    │  - is_smoker: bool                                                                     │
    │  - pack_years: float {0..150}                                                          │
    │  - days_since_smoking_change: int                                                      │
    │  - lung_state: LungState [0..1]                                                        │
    │  - diet: Literal["saludable", "normal", "mala"]                                        │
    │  - sensitive_tumor_volume: float {≥0}                                                  │
    │  - resistant_tumor_volume: float {≥0}                                                  │
    │  - active_treatment: Literal["ninguno", "quimio", "radio", "inmuno"]                   │
    │  - treatment_days: int {≥0}                                                            │
    │  - mode: Literal["libre", "biblioteca"]                                                │
    │  - case_id: str [0..1]                                                                 │
    ├────────────────────────────────────────────────────────────────────────────────────────┤
    │  «derived» + total_volume: float                                                       │
    │  «derived» + approx_stage: str                                                         │
    │  + compute_risk_score(): float                                                         │
    │  + update_lung_state(): LungState                                                      │
    └────────────────────────────────────────────────────────────────────────────────────────┘
              │ <<creates>>                           │ <<creates>>
              ▼                                       ▼
    ┌────────────────────────────────────┐    ┌────────────────────────────────────┐
    │         TeacherResponse            │    │       HealthCheckResponse          │
    │         <<value object>>           │    │       <<value object>>             │
    ├────────────────────────────────────┤    ├────────────────────────────────────┤
    │  - explanation: str                │    │  - status: str                     │
    │  - recommendation: str             │    │  - llm_available: bool             │
    │  - sources: List[str]              │    │  - chroma_available: bool          │
    │  - warning: str [0..1]             │    │  - model_loaded: bool              │
    │  - retrieved_chunks: int           │    │  - knowledge_docs: int             │
    │  - llm_model: str                  │    └────────────────────────────────────┘
    │  - processing_time_ms: int         │
    └────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                   <<package>> app.services                                   ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌────────────────────────────────────────────────────────────────────────────────────────┐
    │                                   AITeacherService                                      │
    │                                   <<service>>                                           │
    ├────────────────────────────────────────────────────────────────────────────────────────┤
    │  - settings: Settings                                                                  │
    │  - repository: MedicalKnowledgeRepository                                              │
    │  - llm_client: LLMClient                                                               │
    │  - prompt_templates: PromptTemplates                                                   │
    │  - _response_cache: Dict[str, Tuple[TeacherResponse, float]]                           │
    ├────────────────────────────────────────────────────────────────────────────────────────┤
    │  «async» + get_educational_feedback(state: SimulationState): TeacherResponse           │
    │  - _build_search_query(state: SimulationState): str                                    │
    │  - _filter_and_rerank_chunks(query: str, chunks: List): List                           │
    │  - _is_malicious(text: str): bool                                                      │
    │  - _get_cache_key(state: SimulationState): str                                         │
    │  - _get_cached_response(key: str): TeacherResponse [0..1]                              │
    │  - _cache_response(key: str, response: TeacherResponse): void                          │
    └─────────────────────┬─────────────────────────────────────────┬────────────────────────┘
                          │ <<dependency>>                          │ <<dependency>>
                          ▼                                         ▼
    ┌────────────────────────────────────┐          ┌────────────────────────────────────┐
    │     MedicalKnowledgeRepository     │          │     <<interface>> LLMClient        │
    │     <<repository>>                 │          ├────────────────────────────────────┤
    ├────────────────────────────────────┤          │ «async» + query(prompt: str): str  │
    │  - _client: chromadb.Client        │          │  + check_availability(): bool      │
    │  - _collection: Collection         │          └─────────────────┬──────────────────┘
    │  - _embedding_model: SentenceTransf│                            │ <<realizes>>
    ├────────────────────────────────────┤                  ┌─────────┴─────────┐
    │  + initialize(): void              │                  ▼                   ▼
    │  + retrieve_relevant_chunks(): List│    ┌──────────────────────┐ ┌──────────────────────┐
    │  + add_documents(): void           │    │    OllamaClient      │ │      MockLLM         │
    │  + get_collection_stats(): dict    │    │    <<adapter>>       │ │    <<test double>>   │
    │  + close(): void                   │    ├──────────────────────┤ ├──────────────────────┤
    └────────────────────────────────────┘    │ - base_url: str      │ │ - responses: Dict    │
                                              │ - model: str         │ └──────────────────────┘
                                              │ - timeout: int       │
                                              └──────────────────────┘
```

---

## 3. Diagrama de Clases - Cliente Unity (C#)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DIAGRAMA DE CLASES UML                                        │
│                                 Subsistema: Cliente Unity (C#)                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<package>> LungCancerVR.MathModel                              ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────┐
    │   <<enumeration>> DietType      │
    ├─────────────────────────────────┤
    │   Healthy                       │
    │   Normal                        │
    │   Poor                          │
    └────────────────┬────────────────┘
                     │ <<uses>>
                     ▼
    ┌───────────────────────────────────────────────────────────────────────────────────────┐
    │                                  PatientProfile                                        │
    │                                  <<entity>>                                            │
    ├───────────────────────────────────────────────────────────────────────────────────────┤
    │  + Age: int                                                                           │
    │  + IsSmoker: bool                                                                     │
    │  + PackYears: float                                                                   │
    │  + Diet: DietType                                                                     │
    │  + GeneticFactor: float = 1.0                                                         │
    ├───────────────────────────────────────────────────────────────────────────────────────┤
    │  + GetAgeGrowthModifier(): float                                                      │
    │  + GetSmokingCapacityModifier(): float                                                │
    │  + GetDietModifier(): float                                                           │
    │  + GetCombinedModifier(): float                                                       │
    │  + IsValid(out error: string): bool                                                   │
    └────────────────────────────────────────────┬──────────────────────────────────────────┘
                                                 │ 1
                                                 │ <<composition>>
                                                 ▼
    ┌───────────────────────────────────────────────────────────────────────────────────────┐
    │                                 TumorGrowthModel                                       │
    │                                 <<domain service>>                                     │
    ├───────────────────────────────────────────────────────────────────────────────────────┤
    │  + SensitiveCells: float {Ns, cm³}        // Ecuación: dNs/dt = rs·Ns·ln(K/(Ns+Nr))  │
    │  + ResistantCells: float {Nr, cm³}        // Ecuación: dNr/dt = rr·Nr·ln(K/(Ns+Nr))  │
    │  «derived» + TotalVolume: float                                                       │
    │  + CurrentTime: float {días}                                                          │
    │  + TreatmentStartTime: float                                                          │
    │  - K: float {capacidad de carga, cm³}                                                 │
    │  - rs_base: float = 0.012 {tasa crecimiento sensibles, día⁻¹}                         │
    │  - rr_base: float = 0.008 {tasa crecimiento resistentes, día⁻¹}                       │
    │  - mutationRate: float = 1e-6                                                         │
    │  - patient: PatientProfile                                                            │
    │  - treatment: ITreatmentStrategy                                                      │
    │  - solver: RK4Solver                                                                  │
    ├───────────────────────────────────────────────────────────────────────────────────────┤
    │  + Simulate(days: float): void                                                        │
    │  + SetTreatment(strategy: ITreatmentStrategy): void                                   │
    │  + ComputeDerivatives(t: float, y: float[]): float[]                                  │
    │  + GetAdjustedGrowthRate(): float                                                     │
    │  + GetProjection(daysAhead: int): List<SimulationPoint>                               │
    │  + Reset(): void                                                                      │
    └────────────────────┬────────────────────────────────────────────┬─────────────────────┘
                         │ 1                                          │ 1
                         │ <<composition>>                            │ <<aggregation>>
                         ▼                                            ▼
    ┌────────────────────────────────────┐       ┌──────────────────────────────────────────┐
    │            RK4Solver               │       │     <<interface>> ITreatmentStrategy     │
    │            <<utility>>             │       ├──────────────────────────────────────────┤
    ├────────────────────────────────────┤       │  «readonly» + Name: string               │
    │  - _stepSize: float = 0.1          │       │  «readonly» + CycleDuration: float       │
    │  - _derivativeFunc: Func<>         │       │  «readonly» + MaxEfficacy: float         │
    ├────────────────────────────────────┤       │  + GetBeta(time: float): float           │
    │  + Solve(t0, y0, tEnd): float[]    │       └──────────────────────┬───────────────────┘
    │  + Step(t, y): float[]             │                              │
    └────────────────────────────────────┘                              │ <<realizes>>
                                                           ┌────────────┼────────────┐
                                                           │            │            │
                                                           ▼            ▼            ▼
    ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
    │   NoTreatmentStrategy     │ │   ChemotherapyStrategy    │ │   RadiotherapyStrategy    │
    │   <<concrete>>            │ │   <<concrete>>            │ │   <<concrete>>            │
    ├───────────────────────────┤ ├───────────────────────────┤ ├───────────────────────────┤
    │                           │ │  Ciclo: 21 días           │ │  Sesiones: 25-30          │
    │  β(t) = 0                 │ │  Eficacia: 75%            │ │  Eficacia: 80%            │
    │                           │ │                           │ │                           │
    │  (Sin tratamiento)        │ │  β(t) = βₘₐₓ(1-e^{-kt})   │ │  β(t) = pulso durante     │
    │                           │ │       × (1-0.1×ciclo)     │ │         sesión activa     │
    └───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
                                                                            │
                                                           ┌────────────────┘
                                                           ▼
                                  ┌───────────────────────────┐
                                  │  ImmunotherapyStrategy    │
                                  │  <<concrete>>             │
                                  ├───────────────────────────┤
                                  │  Ciclo: 14-21 días        │
                                  │  Eficacia: 40%            │
                                  │                           │
                                  │  β(t) = βₘₐₓ(1-e^{-kt})   │
                                  │       × activación inmune │
                                  └───────────────────────────┘
```

---

## 4. Diagrama de Estados - LungState

El sistema modela la condición pulmonar como una **máquina de estados finitos (FSM)**. Las transiciones dependen de métricas calculadas: `risk_score`, `total_volume`, y `growth_rate`.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               DIAGRAMA DE ESTADOS UML - LungState                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                                         ●
                                         │
                                         │ [tumor_volume == 0]
                                         ▼
                              ╔════════════════════════╗
                              ║         SANO           ║
                              ║    (estado inicial)    ║
                              ╚════════════╤═══════════╝
                                           │
               ┌───────────────────────────┼───────────────────────────┐
               │                           │                           │
               │ [risk_score > 0.5         │ [tumor_volume > 0         │
               │  AND volume == 0]         │  AND risk_score ≤ 0.5]    │
               ▼                           │                           ▼
    ╔════════════════════════╗             │            ╔════════════════════════╗
    ║      EN_RIESGO         ║             │            ║        ESTABLE         ║
    ║  (fumador/edad alta)   ║             │            ║   (tumor controlado)   ║
    ╚════════════╤═══════════╝             │            ╚════════════╤═══════════╝
                 │                         │                         │
                 │ [volume > 0]            │                         │ [growth_rate > 1.1]
                 │                         │                         │
                 └─────────────────────────┼─────────────────────────┘
                                           │
                                           ▼
                              ╔════════════════════════╗
                              ║      PROGRESANDO       ║◀──────────────────────────┐
                              ║   (tumor en avance)    ║                           │
                              ╚════════════╤═══════════╝                           │
                                           │                                       │
               ┌───────────────────────────┼───────────────────────────┐           │
               │                           │                           │           │
               │ [tratamiento efectivo:    │ [volume > 100cm³          │           │
               │  growth_rate < 0.9]       │  OR resistance > 50%]     │           │
               ▼                           │                           ▼           │
    ╔════════════════════════╗             │            ╔════════════════════════╗ │
    ║        ESTABLE         ║             │            ║        CRITICO         ║ │
    ║     (en remisión)      ║─────────────┘            ║  (pronóstico grave)    ║─┘
    ╚════════════════════════╝                          ╚════════════╤═══════════╝
                                                                     │ [tratamiento
                                                                     │  muy efectivo]
                                                                     │
                                                                     │ [volume > 500cm³
                                                                     │  OR metástasis]
                                                                     ▼
                                                        ╔════════════════════════╗
                                                        ║       TERMINAL         ║
                                                        ║    (estado final)      ║
                                                        ╚════════════════════════╝
                                                                     │
                                                                     ▼
                                                                     ◉

```

### Tabla de Transiciones

| Estado Origen | Guardia (Condición) | Estado Destino | Acción |
|---------------|---------------------|----------------|--------|
| **SANO** | `risk_score > 0.5 ∧ volume = 0` | EN_RIESGO | Alertar factores de riesgo |
| **SANO** | `volume > 0` | ESTABLE | Iniciar monitoreo |
| **EN_RIESGO** | `volume > 0` | PROGRESANDO | Iniciar tratamiento |
| **ESTABLE** | `growth_rate > 1.1` | PROGRESANDO | Escalar tratamiento |
| **PROGRESANDO** | `growth_rate < 0.9` | ESTABLE | Continuar tratamiento |
| **PROGRESANDO** | `volume > 100 ∨ resistance > 50%` | CRITICO | Tratamiento agresivo |
| **CRITICO** | `tratamiento muy efectivo` | PROGRESANDO | Reducir intensidad |
| **CRITICO** | `volume > 500 ∨ metástasis` | TERMINAL | Cuidados paliativos |

---

## 5. Patrones de Diseño Aplicados

| Patrón | Elemento | Justificación |
|--------|----------|---------------|
| **Strategy** | `ITreatmentStrategy` | Intercambiar algoritmos de tratamiento sin modificar `TumorGrowthModel` (OCP) |
| **Repository** | `MedicalKnowledgeRepository` | Abstraer acceso a ChromaDB, facilitar testing |
| **Dependency Injection** | `AITeacherService(repo, llm)` | Invertir dependencias, facilitar mocks (DIP) |
| **Singleton** | `get_settings()`, `get_repository()` | Reutilizar recursos costosos (conexiones, modelos) |
| **Value Object** | `TeacherResponse`, `SimulationState` | Inmutabilidad, validación automática (Pydantic) |
| **Adapter** | `OllamaClient` | Adaptar API HTTP de Ollama a interfaz `LLMClient` |
| **Template Method** | Prompt building en `PromptTemplates` | Estructura fija con partes variables |

---

## 6. Matriz de Clases por Responsabilidad

| Clase | Tipo | Responsabilidad | Capa |
|-------|------|-----------------|------|
| `SimulationState` | Entity | Representar estado de simulación | Modelo |
| `TeacherResponse` | Value Object | Representar respuesta educativa | Modelo |
| `LungState` | Enum | Definir estados posibles del pulmón | Modelo |
| `AITeacherService` | Service | Orquestar pipeline RAG+LLM | Servicio |
| `MedicalKnowledgeRepository` | Repository | Acceder a base vectorial | Infraestructura |
| `OllamaClient` | Adapter | Comunicar con LLM | Infraestructura |
| `TumorGrowthModel` | Domain Service | Ejecutar simulación matemática | Dominio |
| `PatientProfile` | Entity | Representar perfil del paciente | Modelo |
| `RK4Solver` | Utility | Resolver ecuaciones diferenciales | Utilidad |
| `ITreatmentStrategy` | Interface | Definir contrato de tratamientos | Abstracción |

---

*Documento generado siguiendo el estándar 4+1 de Kruchten (IEEE Software, 1995)*
