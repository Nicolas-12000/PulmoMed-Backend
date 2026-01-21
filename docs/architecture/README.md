# Documentación de Arquitectura - Modelo 4+1 de Kruchten

## Modelo de Vistas Arquitectónicas

Esta documentación sigue el modelo **4+1 de Philippe Kruchten** (IEEE Software, Vol. 12, No. 6, Noviembre 1995), estándar de la industria para describir arquitecturas de software intensivo mediante vistas concurrentes.

> *"La arquitectura del software se ocupa del diseño y la implementación de la estructura de alto nivel del software. Es el resultado de ensamblar un cierto número de elementos arquitectónicos de alguna forma bien elegida para satisfacer la funcionalidad principal y los requisitos de rendimiento del sistema, así como algunos otros requisitos no funcionales."*
> — Philippe Kruchten

---

## Diagrama del Modelo 4+1

```
                                    ┌─────────────────────────────────┐
                                    │     VISTA DE ESCENARIOS (+1)    │
                                    │                                 │
                                    │   • Casos de Uso principales    │
                                    │   • Escenarios de validación    │
                                    │   • Requisitos funcionales      │
                                    │                                 │
                                    │   Audiencia: Todos los          │
                                    │   stakeholders                  │
                                    └────────────────┬────────────────┘
                                                     │
                          ┌──────────────────────────┼──────────────────────────┐
                          │                          │                          │
                          ▼                          ▼                          ▼
          ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
          │      VISTA LÓGICA         │  │    VISTA DE PROCESOS      │  │      VISTA FÍSICA         │
          │                           │  │                           │  │                           │
          │ • Diagrama de Clases      │  │ • Diagrama de Secuencia   │  │ • Diagrama de Despliegue  │
          │ • Diagrama de Estados     │  │ • Diagrama de Actividad   │  │                           │
          │                           │  │ • Diagrama de Comunicación│  │ Nodos de hardware,        │
          │ Funcionalidad para        │  │                           │  │ topología de red,         │
          │ usuarios finales          │  │ Comportamiento dinámico,  │  │ mapeo de componentes      │
          │                           │  │ concurrencia, rendimiento │  │                           │
          │ Audiencia: Usuarios,      │  │                           │  │ Audiencia: Ingenieros     │
          │ Diseñadores               │  │ Audiencia: Integradores,  │  │ de sistemas, DevOps       │
          │                           │  │ Desarrolladores           │  │                           │
          └───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────┐
          │   VISTA DE DESARROLLO     │
          │                           │
          │ • Diagrama de Paquetes    │
          │ • Diagrama de Componentes │
          │                           │
          │ Organización del código,  │
          │ módulos, dependencias     │
          │                           │
          │ Audiencia: Programadores, │
          │ Gestores de proyecto      │
          └───────────────────────────┘
```

---

## Índice de Documentos

| Vista | Archivo | Propósito | Diagramas UML | Audiencia |
|-------|---------|-----------|---------------|-----------|
| **Lógica** | [01_LOGICAL_VIEW.md](01_LOGICAL_VIEW.md) | Estructura estática, funcionalidad | Clases, Estados | Usuarios, Diseñadores |
| **Desarrollo** | [02_DEVELOPMENT_VIEW.md](02_DEVELOPMENT_VIEW.md) | Organización del código | Paquetes, Componentes | Programadores, QA |
| **Procesos** | [03_PROCESS_VIEW.md](03_PROCESS_VIEW.md) | Comportamiento dinámico, concurrencia | Secuencia, Actividad | Integradores, DevOps |
| **Física** | [04_PHYSICAL_VIEW.md](04_PHYSICAL_VIEW.md) | Topología de despliegue | Despliegue | Ing. de Sistemas |
| **Escenarios** | [05_SCENARIOS_VIEW.md](05_SCENARIOS_VIEW.md) | Validación de arquitectura | Casos de Uso | Todos |

---

## Sistema PulmoMed

### Descripción

**PulmoMed** es un simulador educativo de crecimiento tumoral pulmonar en realidad virtual, con asistente pedagógico inteligente basado en RAG (Retrieval-Augmented Generation) y LLM (Large Language Model).

### Propósito Educativo

Permite a estudiantes de medicina:
1. Visualizar la progresión tumoral en 3D inmersivo
2. Experimentar con diferentes tratamientos oncológicos
3. Recibir explicaciones pedagógicas contextualizadas
4. Estudiar casos clínicos de una biblioteca curada

### Arquitectura de Alto Nivel

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ARQUITECTURA PULMOMED                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────────────┐                    ┌─────────────────────────────────────────────┐
     │     CLIENTE VR          │                    │              BACKEND IA                     │
     │     (Meta Quest 3)      │                    │              (Servidor)                     │
     │                         │    HTTP/REST       │                                             │
     │  ┌───────────────────┐  │    JSON            │  ┌─────────────────────────────────────────┐│
     │  │   Unity 2022.3    │  │◀──────────────────▶│  │            FastAPI + Uvicorn            ││
     │  │   + XR Toolkit    │  │    Port 8000       │  │                                         ││
     │  └───────────────────┘  │                    │  └────────────────────┬────────────────────┘│
     │           │             │                    │                       │                     │
     │           ▼             │                    │           ┌───────────┴───────────┐         │
     │  ┌───────────────────┐  │                    │           ▼                       ▼         │
     │  │  C# MathModel     │  │                    │  ┌─────────────────┐    ┌─────────────────┐ │
     │  │  (Gompertz + RK4) │  │                    │  │   RAG Engine    │    │   LLM Client    │ │
     │  │                   │  │                    │  │   (ChromaDB)    │    │   (Ollama)      │ │
     │  │  • Simulación     │  │                    │  │                 │    │                 │ │
     │  │  • Tratamientos   │  │                    │  │  BGE-M3         │    │  llama3.2       │ │
     │  │  • Visualización  │  │                    │  │  embeddings     │    │  7B params      │ │
     │  └───────────────────┘  │                    │  └─────────────────┘    └─────────────────┘ │
     │                         │                    │                                             │
     └─────────────────────────┘                    └─────────────────────────────────────────────┘
```

### Stack Tecnológico

| Capa | Tecnología | Versión | Propósito |
|------|------------|---------|-----------|
| **Cliente VR** | Unity + XR Toolkit | 2022.3 LTS | Renderizado 3D, interacción VR |
| **Modelo Matemático** | C# (.NET Standard 2.1) | - | Ecuaciones Gompertz, solver RK4 |
| **API REST** | FastAPI + Uvicorn | 0.109.0 | Endpoints HTTP, validación |
| **Base Vectorial** | ChromaDB | 0.4.22 | Almacenamiento de embeddings |
| **Embeddings** | sentence-transformers (BGE-M3) | latest | Vectorización de texto |
| **LLM Local** | Ollama (llama3.2) | latest | Generación de respuestas |
| **Validación** | Pydantic | 2.5.3 | Esquemas de datos |
| **Contenedores** | Docker + Docker Compose | - | Despliegue |

---

## Principios Arquitectónicos

### SOLID

| Principio | Aplicación en PulmoMed |
|-----------|------------------------|
| **S**ingle Responsibility | Cada clase tiene una responsabilidad: `TumorGrowthModel` solo simula, `AITeacherService` solo orquesta |
| **O**pen/Closed | `ITreatmentStrategy` permite añadir tratamientos sin modificar el modelo |
| **L**iskov Substitution | `MockLLM` puede sustituir a `OllamaClient` en tests |
| **I**nterface Segregation | Interfaces pequeñas: `LLMClient` solo tiene `query()` y `check_availability()` |
| **D**ependency Inversion | `AITeacherService` depende de abstracciones (`LLMClient`, `Repository`) |

### Atributos de Calidad

| Atributo | Táctica Arquitectónica | Medida |
|----------|------------------------|--------|
| **Rendimiento** | Caché LRU en respuestas, async I/O | < 15s E2E, < 100ms cache hit |
| **Disponibilidad** | Fallback responses, graceful degradation | Respuesta siempre, aunque degradada |
| **Testabilidad** | Inyección de dependencias, mocks | 85%+ cobertura |
| **Modificabilidad** | Strategy Pattern, Repository Pattern | Nuevos tratamientos/LLMs sin cambios |
| **Usabilidad** | Validación con mensajes claros, timeout VR | Errores descriptivos |

---

## Referencias

1. Kruchten, P. (1995). *Architectural Blueprints—The "4+1" View Model of Software Architecture*. IEEE Software, 12(6), 42-50.
2. Bass, L., Clements, P., & Kazman, R. (2012). *Software Architecture in Practice* (3rd ed.). Addison-Wesley.
3. Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.

---

*Documento de Arquitectura de Software PulmoMed v2.0*
*Última actualización: Enero 2026*
