# Vista de Desarrollo - Modelo 4+1 de Kruchten

> **Propósito**: Describir la organización del sistema desde la perspectiva del programador, mostrando la estructura del código fuente, módulos, dependencias y gestión del software.
>
> **Audiencia**: Programadores, Gestores de proyecto, QA.
>
> **Diagramas UML**: Diagrama de Paquetes, Diagrama de Componentes.

---

## 1. Introducción

La Vista de Desarrollo (también llamada Vista de Implementación) muestra cómo está particionado el software en módulos y cómo se relacionan entre sí. En PulmoMed existen dos bases de código:

| Codebase | Lenguaje | Propósito | Líneas de Código (aprox.) |
|----------|----------|-----------|--------------------------|
| **Backend Python** | Python 3.11 | API REST, RAG, LLM | ~2,500 LOC |
| **CSharp_MathModel** | C# (.NET Standard 2.1) | Simulación matemática | ~1,200 LOC |

Esta vista responde a la pregunta: *"¿Cómo está organizado el código?"*

---

## 2. Diagrama de Paquetes - Backend Python

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DIAGRAMA DE PAQUETES UML                                      │
│                                    Backend Python (FastAPI)                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<system>> PulmoMed-Backend                                     ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │                                 <<layer>> PRESENTACIÓN                                       │
    │  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
    │  │                              <<package>> app.api                                       │  │
    │  ├───────────────────────────────────────────────────────────────────────────────────────┤  │
    │  │  • teacher_endpoint.py      → POST /api/v1/consultar_profesor                         │  │
    │  │  • auth_endpoint.py         → POST /auth/login, /auth/register                        │  │
    │  │  • course_endpoint.py       → CRUD /courses                                           │  │
    │  │  • exam_endpoint.py         → CRUD /exams                                             │  │
    │  │  • stats_endpoint.py        → GET /stats                                              │  │
    │  │  • rate_limiter.py          → Middleware de rate limiting                             │  │
    │  └───────────────────────────────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                   │
                                                   │ <<import>>
                                                   ▼
    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │                               <<layer>> LÓGICA DE NEGOCIO                                    │
    │  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
    │  │                            <<package>> app.services                                    │  │
    │  ├───────────────────────────────────────────────────────────────────────────────────────┤  │
    │  │  • teacher_service.py           → AITeacherService (orquestación RAG+LLM)             │  │
    │  │  • auth_service.py              → Autenticación y autorización                        │  │
    │  │  • course_service.py            → Gestión de cursos                                   │  │
    │  │  • exam_service.py              → Gestión de exámenes                                 │  │
    │  │  • stats_service.py             → Estadísticas y métricas                             │  │
    │  │  • simulation_history_service.py → Historial de simulaciones                          │  │
    │  │  • ai_question_service.py       → Generación de preguntas con IA                      │  │
    │  │  • interfaces.py                → Protocols/Interfaces abstractas                     │  │
    │  └───────────────────────────────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                   │
                       ┌───────────────────────────┼───────────────────────────┐
                       │ <<import>>                │ <<import>>                │ <<import>>
                       ▼                           ▼                           ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │  <<package>> app.repositories│ │   <<package>> app.llm       │ │   <<package>> app.rag       │
    ├─────────────────────────────┤ ├─────────────────────────────┤ ├─────────────────────────────┤
    │ • medical_knowledge_repo.py │ │ • interface.py              │ │ • prompts.py                │
    │   → Abstracción ChromaDB    │ │   → Protocol LLMClient      │ │   → Templates de prompts    │
    │   → Embeddings BGE-M3       │ │ • ollama_client.py          │ │ • loader.py                 │
    │                             │ │   → Implementación real     │ │   → Indexación de PDFs      │
    │                             │ │ • mock_llm.py               │ │                             │
    │                             │ │   → Mock para testing       │ │                             │
    └─────────────────────────────┘ └─────────────────────────────┘ └─────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │                                 <<layer>> CROSS-CUTTING                                      │
    │  ┌────────────────────────────────────────┐  ┌────────────────────────────────────────────┐ │
    │  │      <<package>> app.models            │  │        <<package>> app.core                │ │
    │  ├────────────────────────────────────────┤  ├────────────────────────────────────────────┤ │
    │  │ • simulation_state.py                  │  │ • config.py                                │ │
    │  │   → SimulationState, TeacherResponse   │  │   → Settings (pydantic-settings)           │ │
    │  │   → LungState enum                     │  │   → Variables de entorno                   │ │
    │  │ • db_models.py                         │  │ • database.py                              │ │
    │  │   → SQLAlchemy models                  │  │   → Conexión a base de datos               │ │
    │  └────────────────────────────────────────┘  │ • security.py                              │ │
    │                                              │   → JWT, hashing, autenticación            │ │
    │  ┌────────────────────────────────────────┐  └────────────────────────────────────────────┘ │
    │  │      <<package>> app.schemas           │                                                 │
    │  ├────────────────────────────────────────┤                                                 │
    │  │ • auth_schemas.py                      │                                                 │
    │  │ • course_schemas.py                    │                                                 │
    │  │ • exam_schemas.py                      │                                                 │
    │  │ • stats_schemas.py                     │                                                 │
    │  └────────────────────────────────────────┘                                                 │
    └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Diagrama de Paquetes - Cliente Unity (C#)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DIAGRAMA DE PAQUETES UML                                      │
│                                    Cliente Unity (C#)                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<system>> LungCancerVR.MathModel                               ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
    │   <<package>> Core        │    │   <<package>> Models      │    │  <<package>> Solvers      │
    ├───────────────────────────┤    ├───────────────────────────┤    ├───────────────────────────┤
    │ • TumorGrowthModel.cs     │◀───│ • PatientProfile.cs       │    │ • RK4Solver.cs            │
    │   → Modelo Gompertz       │    │   → Perfil del paciente   │───▶│   → Runge-Kutta 4º orden  │
    │   → Ecuaciones            │    │ • SimulationState.cs      │    │   → Step adaptativo       │
    │     diferenciales         │    │   → Estado serializable   │    │                           │
    │ • SimulationHistory.cs    │    │                           │    │                           │
    │   → Historial de estados  │    │                           │    │                           │
    └───────────────────────────┘    └───────────────────────────┘    └───────────────────────────┘
             │
             │ <<uses>>
             ▼
    ┌───────────────────────────┐    ┌───────────────────────────┐
    │ <<package>> Treatments    │    │   <<package>> Tests       │
    ├───────────────────────────┤    ├───────────────────────────┤
    │ • ITreatmentStrategy.cs   │    │ • TumorGrowthModelTests   │
    │   → Interface Strategy    │    │ • PatientProfileTests     │
    │ • ChemotherapyStrategy    │    │ • RK4SolverTests          │
    │ • RadiotherapyStrategy    │    │ • IntegrationTests        │
    │ • ImmunotherapyStrategy   │    │                           │
    │ • NoTreatmentStrategy     │    │                           │
    └───────────────────────────┘    └───────────────────────────┘

    ┌───────────────────────────┐
    │  <<package>> Examples     │
    ├───────────────────────────┤
    │ • BasicSimulation.cs      │
    │ • TreatmentComparison.cs  │
    │ • BackendIntegration.cs   │
    │ • HistoryExample.cs       │
    └───────────────────────────┘
```

---

## 4. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  DIAGRAMA DE COMPONENTES UML                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<subsystem>> Backend Python                                    ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │                              <<component>> FastAPI Application                               │
    │                                                                                              │
    │    ○──────────────── REST API ─────────────────────────────────────────────────────────────▶│
    │    (provided interface)                                                                      │
    │                                                                                              │
    │    Endpoints expuestos:                                                                      │
    │    • POST /api/v1/consultar_profesor                                                         │
    │    • GET  /api/v1/library_cases/{id}                                                         │
    │    • GET  /health                                                                            │
    │    • POST /auth/login                                                                        │
    │    • POST /auth/register                                                                     │
    │                                                                                              │
    └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                   │
                                                   ● (required: AITeacherService)
                                                   │
                                                   ▼
    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │                            <<component>> AITeacher Service                                   │
    │                                                                                              │
    │    ○──────────────── Educational Feedback ─────────────────────────────────────────────────▶│
    │    (provided interface)                                                                      │
    │                                                                                              │
    │    Operaciones:                                                                              │
    │    • get_educational_feedback(SimulationState) → TeacherResponse                            │
    │                                                                                              │
    └─────────────────────┬───────────────────────────────────────────────────┬───────────────────┘
                          │                                                   │
              ● (required)│                                       ● (required)│
                          ▼                                                   ▼
    ┌─────────────────────────────────────────┐    ┌─────────────────────────────────────────────┐
    │        <<component>> RAG Engine         │    │          <<component>> LLM Client           │
    │                                         │    │                                             │
    │    ○── Vector Search ────────────▶      │    │    ○── LLM Query ─────────────────▶        │
    │    (provided)                           │    │    (provided)                               │
    │                                         │    │                                             │
    │    ● chromadb (external)                │    │    ● ollama HTTP (external)                 │
    │    ● sentence-transformers (library)    │    │                                             │
    │                                         │    │    Implementaciones:                        │
    │    Operaciones:                         │    │    • OllamaClient (producción)              │
    │    • retrieve_relevant_chunks(query)    │    │    • MockLLM (testing)                      │
    │    • add_documents(docs)                │    │                                             │
    └─────────────────────────────────────────┘    └─────────────────────────────────────────────┘


    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<subsystem>> Cliente Unity                                     ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────────────┐
    │  <<component>> VR Engine    │  │ <<component>> MathModel     │  │ <<component>> Network       │
    │                             │  │                             │  │     Client                  │
    │  ○── 3D Rendering ──▶       │  │  ○── Simulation ──▶         │  │                             │
    │  ○── User Input ──▶         │  │  (provided)                 │  │  ○── HTTP Client ──▶        │
    │  (provided)                 │  │                             │  │  (provided)                 │
    │                             │  │  • Gompertz equations       │  │                             │
    │  ● Unity XR Toolkit         │  │  • RK4 numerical solver     │  │  ● REST API (required)      │
    │  ● Meta Quest SDK           │  │  • Treatment strategies     │  │                             │
    └─────────────────────────────┘  └─────────────────────────────┘  └─────────────────────────────┘


    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<subsystem>> Servicios Externos                                ║
    ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────┐  ┌─────────────────────────────┐
    │ <<component>> ChromaDB      │  │ <<component>> Ollama        │
    │                             │  │                             │
    │ ○── Vector Storage ──▶      │  │ ○── LLM Inference ──▶       │
    │                             │  │                             │
    │ Puerto: 8001                │  │ Puerto: 11434               │
    │ Protocolo: HTTP             │  │ Protocolo: HTTP             │
    │                             │  │ Modelo: llama3.2 (7B)       │
    └─────────────────────────────┘  └─────────────────────────────┘


    ╭─────────────────────────────────────────────────────────────────────────────────────────────╮
    │                                         LEYENDA                                              │
    ├─────────────────────────────────────────────────────────────────────────────────────────────┤
    │    ○──▶   Interfaz proporcionada (provided interface)                                       │
    │    ●      Interfaz requerida (required interface)                                           │
    │    ──▶    Dependencia                                                                        │
    ╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 5. Estructura de Directorios

```
PulmoMed-Backend/
│
├── main.py                           # Entry point FastAPI
├── requirements.txt                  # Dependencias Python (pip)
├── docker-compose.yml                # Orquestación de contenedores
├── pytest.ini                        # Configuración pytest
├── mypy.ini                          # Configuración type checking
│
├── app/                              # ══════════ CÓDIGO PRINCIPAL ══════════
│   ├── __init__.py
│   │
│   ├── api/                          # [CAPA PRESENTACIÓN]
│   │   ├── __init__.py
│   │   ├── teacher_endpoint.py       #   → Endpoint principal (/consultar_profesor)
│   │   ├── auth_endpoint.py          #   → Autenticación
│   │   ├── course_endpoint.py        #   → Gestión de cursos
│   │   ├── exam_endpoint.py          #   → Gestión de exámenes
│   │   ├── stats_endpoint.py         #   → Estadísticas
│   │   └── rate_limiter.py           #   → Rate limiting middleware
│   │
│   ├── services/                     # [CAPA LÓGICA DE NEGOCIO]
│   │   ├── __init__.py
│   │   ├── teacher_service.py        #   → AITeacherService (pipeline RAG+LLM)
│   │   ├── auth_service.py           #   → Autenticación/Autorización
│   │   ├── course_service.py         #   → Lógica de cursos
│   │   ├── exam_service.py           #   → Lógica de exámenes
│   │   ├── stats_service.py          #   → Lógica de estadísticas
│   │   ├── ai_question_service.py    #   → Generación de preguntas IA
│   │   ├── simulation_history_service.py
│   │   └── interfaces.py             #   → Protocols abstractos
│   │
│   ├── repositories/                 # [CAPA ACCESO A DATOS]
│   │   ├── __init__.py
│   │   └── medical_knowledge_repo.py #   → Abstracción ChromaDB
│   │
│   ├── llm/                          # [INTEGRACIÓN LLM]
│   │   ├── __init__.py
│   │   ├── interface.py              #   → Protocol LLMClient
│   │   ├── ollama_client.py          #   → Implementación Ollama
│   │   └── mock_llm.py               #   → Mock para testing
│   │
│   ├── rag/                          # [SISTEMA RAG]
│   │   ├── __init__.py
│   │   ├── prompts.py                #   → Templates de prompts
│   │   └── loader.py                 #   → Indexador de documentos
│   │
│   ├── models/                       # [MODELOS DE DOMINIO]
│   │   ├── __init__.py
│   │   ├── simulation_state.py       #   → SimulationState, TeacherResponse
│   │   └── db_models.py              #   → Modelos SQLAlchemy
│   │
│   ├── schemas/                      # [ESQUEMAS PYDANTIC]
│   │   ├── __init__.py
│   │   ├── auth_schemas.py
│   │   ├── course_schemas.py
│   │   ├── exam_schemas.py
│   │   └── stats_schemas.py
│   │
│   └── core/                         # [CONFIGURACIÓN]
│       ├── __init__.py
│       ├── config.py                 #   → Settings (pydantic-settings)
│       ├── database.py               #   → Conexión DB
│       └── security.py               #   → JWT, hashing
│
├── CSharp_MathModel/                 # ══════════ MODELO MATEMÁTICO C# ══════════
│   ├── Core/
│   │   ├── TumorGrowthModel.cs       #   → Modelo Gompertz polimórfico
│   │   └── SimulationHistory.cs      #   → Historial de estados
│   ├── Models/
│   │   ├── PatientProfile.cs         #   → Perfil del paciente
│   │   └── SimulationState.cs        #   → Estado serializable
│   ├── Solvers/
│   │   └── RK4Solver.cs              #   → Solver Runge-Kutta 4
│   ├── Treatments/
│   │   └── ITreatmentStrategy.cs     #   → Strategy pattern
│   ├── Tests/
│   │   └── *.cs                      #   → Tests unitarios
│   └── Examples/
│       └── *.cs                      #   → Ejemplos de uso
│
├── knowledge_base/                   # ══════════ BASE DE CONOCIMIENTO ══════════
│   ├── casos_biblioteca.json         #   → Casos clínicos curados
│   └── embeddings/
│       └── chroma.sqlite3            #   → Persistencia ChromaDB
│
├── tests/                            # ══════════ TESTS ══════════
│   ├── __init__.py
│   ├── unit/                         #   → Tests unitarios
│   │   ├── test_models.py
│   │   ├── test_service.py
│   │   ├── test_repository.py
│   │   └── ...
│   └── integration/                  #   → Tests de integración
│       ├── test_api.py
│       └── test_rag_e2e.py
│
└── docs/                             # ══════════ DOCUMENTACIÓN ══════════
    └── architecture/                 #   → Modelo 4+1
        ├── README.md
        ├── 01_LOGICAL_VIEW.md
        ├── 02_DEVELOPMENT_VIEW.md
        ├── 03_PROCESS_VIEW.md
        ├── 04_PHYSICAL_VIEW.md
        └── 05_SCENARIOS_VIEW.md
```

---

## 6. Dependencias Externas

### Backend Python (requirements.txt)

| Dependencia | Versión | Propósito | Capa |
|-------------|---------|-----------|------|
| `fastapi` | 0.109.0 | Framework web async | Presentación |
| `uvicorn` | 0.27.0 | ASGI server | Infraestructura |
| `pydantic` | 2.5.3 | Validación de datos | Cross-cutting |
| `pydantic-settings` | 2.1.0 | Configuración | Cross-cutting |
| `chromadb` | 0.4.22 | Base de datos vectorial | Datos |
| `sentence-transformers` | latest | Embeddings BGE-M3 | Datos |
| `httpx` | 0.26.0 | Cliente HTTP async | Infraestructura |
| `python-jose` | 3.3.0 | JWT tokens | Seguridad |
| `passlib` | 1.7.4 | Password hashing | Seguridad |
| `sqlalchemy` | 2.0.25 | ORM | Datos |
| `pytest` | 7.4.4 | Testing | Desarrollo |
| `pytest-asyncio` | 0.23.3 | Testing async | Desarrollo |

### Cliente Unity (C#)

| Dependencia | Versión | Propósito |
|-------------|---------|-----------|
| Unity | 2022.3 LTS | Motor de juego |
| XR Interaction Toolkit | 2.5.x | Interacción VR |
| Meta XR SDK | latest | Soporte Quest 3 |
| Newtonsoft.Json | 13.x | Serialización JSON |

---

## 7. Reglas de Dependencia

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   REGLAS DE DEPENDENCIA                                          │
│                              (Clean Architecture / Onion Architecture)                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────────────────────┐
                              │          PRESENTACIÓN               │
                              │         (app.api.*)                 │
                              │                                     │
                              │  • Depende de Services              │
                              │  • NO conoce implementaciones       │
                              └─────────────────┬───────────────────┘
                                                │
                                                │ puede usar
                                                ▼
                              ┌─────────────────────────────────────┐
                              │        LÓGICA DE NEGOCIO            │
                              │        (app.services.*)             │
                              │                                     │
                              │  • Depende de Interfaces            │
                              │  • Depende de Modelos               │
                              │  • NO conoce FastAPI ni HTTP        │
                              └─────────────────┬───────────────────┘
                                                │
                                                │ puede usar
                                                ▼
                              ┌─────────────────────────────────────┐
                              │           DOMINIO                   │
                              │      (app.models.*, interfaces)     │
                              │                                     │
                              │  • Entidades puras                  │
                              │  • Sin dependencias externas        │
                              │  • Reglas de negocio                │
                              └─────────────────────────────────────┘
                                                ▲
                                                │
                                                │ implementa
                              ┌─────────────────┴───────────────────┐
                              │         INFRAESTRUCTURA             │
                              │   (app.repositories.*, app.llm.*)   │
                              │                                     │
                              │  • Implementa interfaces            │
                              │  • Acceso a DB, APIs externas       │
                              │  • Puede conocer frameworks         │
                              └─────────────────────────────────────┘


    ✅ PERMITIDO:
       • Presentación → Servicios
       • Servicios → Modelos
       • Servicios → Interfaces
       • Infraestructura → Interfaces (implementa)

    ❌ PROHIBIDO:
       • Modelos → Servicios
       • Servicios → Presentación
       • Modelos → Infraestructura
```

---

*Documento generado siguiendo el estándar 4+1 de Kruchten (IEEE Software, 1995)*
