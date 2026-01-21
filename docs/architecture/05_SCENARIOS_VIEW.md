# Vista de Escenarios (+1) - Modelo 4+1 de Kruchten

> **Propósito**: Validar y conectar las cuatro vistas arquitectónicas mediante casos de uso que demuestran que la arquitectura satisface los requisitos funcionales.
>
> **Audiencia**: Todos los stakeholders (usuarios, desarrolladores, gestores).
>
> **Diagramas UML**: Diagrama de Casos de Uso, Escenarios narrativos.

---

## 1. Introducción

La Vista de Escenarios es el "+1" del modelo 4+1. Contiene los casos de uso más importantes que:

1. **Validan** que la arquitectura satisface los requisitos
2. **Conectan** las otras cuatro vistas (Lógica, Desarrollo, Procesos, Física)
3. **Sirven de base** para tests de arquitectura

Según Kruchten: *"Los escenarios son en cierto sentido una abstracción de los requisitos más importantes."*

---

## 2. Diagrama de Casos de Uso

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DIAGRAMA DE CASOS DE USO UML                                        │
│                                    Sistema PulmoMed                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────────────────────────────────────────────────┐
                              │                      Sistema PulmoMed                           │
                              │                                                                 │
                              │   ┌───────────────────────────────────────────────────────────┐│
                              │   │                 Módulo de Simulación                       ││
     ┌───────────────┐        │   │                                                           ││
     │  Estudiante   │        │   │   ┌─────────────────────────┐                             ││
     │  de Medicina  │────────┼──▶│   │      «UC-01»            │                             ││
     │               │        │   │   │  Ejecutar Simulación    │                             ││
     │ (Meta Quest 3)│        │   │   │       Libre             │                             ││
     │               │        │   │   └───────────┬─────────────┘                             ││
     └───────┬───────┘        │   │               │                                           ││
             │                │   │               │ «include»                                 ││
             │                │   │               ▼                                           ││
             │                │   │   ┌─────────────────────────┐                             ││
             │                │   │   │      «UC-04»            │                             ││
             │                │   │   │  Ajustar Parámetros     │                             ││
             │                │   │   │   de Simulación         │                             ││
             │                │   │   └─────────────────────────┘                             ││
             │                │   │                                                           ││
             ├────────────────┼──▶│   ┌─────────────────────────┐                             ││
             │                │   │   │      «UC-02»            │                             ││
             │                │   │   │  Cargar Caso de         │                             ││
             │                │   │   │     Biblioteca          │                             ││
             │                │   │   └───────────┬─────────────┘                             ││
             │                │   │               │                                           ││
             │                │   │               │ «include»                                 ││
             │                │   │               ▼                                           ││
             │                │   │   ┌─────────────────────────┐                             ││
             │                │   │   │      «UC-05»            │                             ││
             │                │   │   │  Visualizar Progresión  │                             ││
             │                │   │   │      del Tumor          │                             ││
             │                │   │   └─────────────────────────┘                             ││
             │                │   │                                                           ││
             │                │   └───────────────────────────────────────────────────────────┘│
             │                │                                                                 │
             │                │   ┌───────────────────────────────────────────────────────────┐│
             │                │   │              Módulo de IA Educativa                        ││
             │                │   │                                                           ││
             │                │   │   ┌─────────────────────────┐                             ││
             └────────────────┼──▶│   │      «UC-03»            │◀─────────┐                  ││
                              │   │   │  Consultar al Profesor  │          │                  ││
                              │   │   │       Virtual           │          │                  ││
                              │   │   └───────────┬─────────────┘          │                  ││
                              │   │               │                        │                  ││
                              │   │               │ «include»              │                  ││
                              │   │               ▼                        │                  ││
                              │   │   ┌─────────────────────────┐          │                  ││
                              │   │   │      «UC-06»            │          │                  ││
                              │   │   │  Buscar Contexto Médico │          │                  ││
                              │   │   │        (RAG)            │          │                  ││
                              │   │   └─────────────────────────┘          │                  ││
                              │   │                                        │                  ││
                              │   └────────────────────────────────────────│──────────────────┘│
                              │                                            │                   │
                              └────────────────────────────────────────────│───────────────────┘
                                                                           │
                                                          ┌────────────────┘
                                                          │
                              ┌───────────────┐           │           ┌───────────────┐
                              │  Profesor IA  │───────────┘           │   ChromaDB    │
                              │ (Ollama LLM)  │                       │  (RAG Engine) │
                              │               │                       │               │
                              │  «actor»      │                       │   «actor»     │
                              │  secundario   │                       │   secundario  │
                              └───────────────┘                       └───────────────┘
```

---

## 3. Especificación de Casos de Uso

### UC-01: Ejecutar Simulación Libre

| Campo | Descripción |
|-------|-------------|
| **ID** | UC-01 |
| **Nombre** | Ejecutar Simulación Libre |
| **Actor Principal** | Estudiante de Medicina |
| **Descripción** | El estudiante configura un paciente virtual y ejecuta una simulación de crecimiento tumoral |
| **Precondiciones** | • Aplicación VR cargada<br>• Unity runtime activo |
| **Postcondiciones** | • Simulación ejecutándose<br>• Visualización 3D del tumor renderizada |
| **Flujo Principal** | 1. Estudiante abre panel de configuración<br>2. Configura paciente: edad, género, historial de tabaquismo<br>3. Sistema genera `PatientProfile` con valores derivados<br>4. Estudiante presiona "Iniciar Simulación"<br>5. Sistema ejecuta `TumorGrowthModel.Simulate()` con `RK4Solver`<br>6. Sistema renderiza modelo 3D del tumor en tiempo real<br>7. Estudiante observa progresión durante N días simulados |
| **Flujo Alternativo** | 6a. Estudiante pausa simulación → modifica parámetros (UC-04) → retoma paso 5 |
| **Excepciones** | E1. Parámetros inválidos → mostrar mensaje de error |
| **Vistas Involucradas** | Lógica: `TumorGrowthModel`, `RK4Solver`<br>Procesos: Solver loop<br>Física: Quest 3 local |

---

### UC-02: Cargar Caso de Biblioteca

| Campo | Descripción |
|-------|-------------|
| **ID** | UC-02 |
| **Nombre** | Cargar Caso de Biblioteca |
| **Actor Principal** | Estudiante de Medicina |
| **Descripción** | El estudiante carga un caso clínico predefinido de la biblioteca |
| **Precondiciones** | • `knowledge_base/casos_biblioteca.json` indexado en ChromaDB |
| **Postcondiciones** | • Caso clínico cargado<br>• Parámetros preconfigurados listos |
| **Flujo Principal** | 1. Estudiante abre menú "Biblioteca de Casos"<br>2. Sistema muestra lista de casos disponibles (nombre, resumen)<br>3. Estudiante selecciona caso (ej: "María, 58 años, NSCLC estadío II")<br>4. Sistema envía `GET /api/v1/library_cases/{id}`<br>5. Sistema carga `PatientProfile` y `SimulationState` desde respuesta<br>6. Sistema inicializa visualización con estado del caso<br>7. Estudiante puede continuar simulación desde ese punto |
| **Flujo Alternativo** | 3a. No hay casos que coincidan → mostrar mensaje "Sin resultados" |
| **Excepciones** | E1. Error de red → mostrar "No se pudo cargar el caso" |
| **Vistas Involucradas** | Física: ChromaDB<br>Desarrollo: `loader.py`, `medical_knowledge_repo.py` |

---

### UC-03: Consultar al Profesor Virtual

| Campo | Descripción |
|-------|-------------|
| **ID** | UC-03 |
| **Nombre** | Consultar al Profesor Virtual |
| **Actor Principal** | Estudiante de Medicina |
| **Actores Secundarios** | Profesor IA (Ollama LLM), ChromaDB (RAG Engine) |
| **Descripción** | El estudiante consulta al asistente IA para recibir explicación educativa contextualizada |
| **Precondiciones** | • Simulación activa con `SimulationState` válido |
| **Postcondiciones** | • Estudiante recibe `TeacherResponse` con explicación educativa |
| **Flujo Principal** | 1. Estudiante activa consulta (botón VR o comando de voz)<br>2. Unity serializa `SimulationState` actual a JSON<br>3. Unity envía `POST /api/v1/consultar_profesor`<br>4. Backend valida estado con Pydantic<br>5. `AITeacherService` verifica caché<br>6. [CACHE MISS] Ejecuta pipeline RAG (UC-06)<br>7. Construye prompt educativo con contexto<br>8. LLM genera respuesta pedagógica<br>9. Backend parsea y retorna `TeacherResponse`<br>10. Unity muestra explicación en panel 3D |
| **Flujo Alternativo** | 5a. [CACHE HIT] → Retorna respuesta cacheada (< 100ms)<br>8a. Timeout LLM (> 15s) → Retornar respuesta fallback |
| **Excepciones** | E1. ChromaDB no disponible → Continuar sin contexto RAG<br>E2. Ollama no disponible → Usar MockLLM |
| **Vistas Involucradas** | **TODAS** (escenario principal de validación) |

---

### UC-04: Ajustar Parámetros de Simulación

| Campo | Descripción |
|-------|-------------|
| **ID** | UC-04 |
| **Actor Principal** | Estudiante de Medicina |
| **Descripción** | El estudiante modifica parámetros de la simulación en curso |
| **Precondiciones** | • Simulación pausada o en configuración inicial |
| **Postcondiciones** | • Nuevos parámetros aplicados al modelo |
| **Flujo Principal** | 1. Estudiante abre panel de parámetros<br>2. Sistema muestra sliders/inputs para: tasa de crecimiento, capacidad de carga, tipo de tratamiento<br>3. Estudiante modifica valores<br>4. Sistema valida rangos (volumen ≥ 0, edad 18-100)<br>5. Sistema actualiza `TumorGrowthModel` con nuevos valores<br>6. Sistema recalcula proyección y actualiza visualización |
| **Excepciones** | E1. Valor fuera de rango → Rechazar cambio, mostrar error |
| **Vistas Involucradas** | Lógica: `PatientProfile`, validadores<br>Desarrollo: `Models/PatientProfile.cs` |

---

### UC-05: Visualizar Progresión del Tumor

| Campo | Descripción |
|-------|-------------|
| **ID** | UC-05 |
| **Actor Principal** | Estudiante de Medicina |
| **Descripción** | El estudiante observa la progresión del tumor en tiempo real |
| **Precondiciones** | • Simulación ejecutada con historial de estados |
| **Postcondiciones** | • Visualización 3D y gráficos actualizados |
| **Flujo Principal** | 1. Sistema ejecuta paso de simulación (`RK4Solver.Step()`)<br>2. Sistema registra nuevo estado en `SimulationHistory`<br>3. Sistema actualiza mesh 3D del tumor (tamaño proporcional a volumen)<br>4. Sistema actualiza gráfico de progresión temporal<br>5. Sistema colorea tumor según `LungState` (verde→amarillo→rojo) |
| **Vistas Involucradas** | Lógica: `SimulationState`, `LungState`<br>Procesos: Render loop |

---

### UC-06: Buscar Contexto Médico (RAG)

| Campo | Descripción |
|-------|-------------|
| **ID** | UC-06 |
| **Actor Principal** | Sistema (interno) |
| **Actores Secundarios** | ChromaDB (RAG Engine) |
| **Descripción** | El sistema busca documentos médicos relevantes para contextualizar la respuesta del LLM |
| **Precondiciones** | • Query de búsqueda construido desde `SimulationState` |
| **Postcondiciones** | • Lista de documentos relevantes recuperados |
| **Flujo Principal** | 1. `AITeacherService` construye query textual desde estado<br>2. `MedicalKnowledgeRepository` genera embedding con BGE-M3 (1024 dims)<br>3. ChromaDB busca top-10 documentos por similaridad coseno<br>4. Service aplica re-ranking por distancia<br>5. Filtra documentos con score < 0.3<br>6. Retorna top-5 documentos más relevantes |
| **Vistas Involucradas** | Física: ChromaDB<br>Desarrollo: `repositories/`, `rag/` |

---

## 4. Escenario Principal: Consulta Educativa Completa

Este escenario **atraviesa todas las vistas** y sirve como validación integral de la arquitectura.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│               ESCENARIO: ESTUDIANTE CONSULTA SOBRE RESISTENCIA AL TRATAMIENTO                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

CONTEXTO:
══════════════════════════════════════════════════════════════════════════════════════════════════
María es estudiante de 3er año de medicina, usando PulmoMed en el laboratorio de simulación VR 
de la universidad. Ha cargado un caso de un paciente fumador de 60 años con tumor en estadío II.
Quiere entender por qué el tumor no responde bien a la radioterapia.
══════════════════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PASO 1: INTERACCIÓN EN VR                                               [Vista Física]         │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ María presiona el botón "Consultar Profesor" en el panel VR del Quest 3.                       │
│ El sistema captura el estado actual de la simulación.                                           │
│                                                                                                 │
│ SimulationState capturado:                                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────────────────────┐    │
│ │  {                                                                                       │    │
│ │    "edad": 60,                                                                           │    │
│ │    "es_fumador": true,                                                                   │    │
│ │    "pack_years": 35,                                                                     │    │
│ │    "volumen_tumor_sensible": 4.5,                                                        │    │
│ │    "volumen_tumor_resistente": 1.2,                                                      │    │
│ │    "tratamiento_activo": "radio",                                                        │    │
│ │    "dias_tratamiento": 15,                                                               │    │
│ │    "modo": "biblioteca"                                                                  │    │
│ │  }                                                                                       │    │
│ └─────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                 │
│ Hardware: Meta Quest 3 → Snapdragon XR2 Gen 2 → WiFi 6E → LAN                                  │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PASO 2: COMUNICACIÓN HTTP                                               [Vista Procesos]       │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ Unity serializa estado y envía request HTTP:                                                    │
│                                                                                                 │
│   POST http://192.168.1.100:8000/api/v1/consultar_profesor                                      │
│   Content-Type: application/json                                                                │
│   Body: { ...SimulationState serializado... }                                                   │
│                                                                                                 │
│ Métricas:                                                                                       │
│ • Tamaño payload: ~500 bytes                                                                    │
│ • Latencia red Quest→Backend: ~15 ms                                                            │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PASO 3: VALIDACIÓN Y ORQUESTACIÓN                                       [Vista Lógica]         │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ FastAPI recibe request:                                                                         │
│   1. Pydantic valida SimulationState → OK                                                       │
│   2. Inyecta dependencias: repository, llm_client                                               │
│   3. Invoca AITeacherService.get_educational_feedback(state)                                    │
│                                                                                                 │
│ Clases involucradas:                                                                            │
│   • SimulationState (entity) → Datos validados                                                  │
│   • AITeacherService (service) → Orquestación                                                   │
│   • MedicalKnowledgeRepository (repository) → Acceso a datos                                    │
│   • OllamaClient (adapter) → Comunicación LLM                                                   │
│                                                                                                 │
│ Patrones aplicados:                                                                             │
│   • Dependency Injection                                                                        │
│   • Repository Pattern                                                                          │
│   • Adapter Pattern                                                                             │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PASO 4: BÚSQUEDA RAG                                                    [Vista Física]         │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ Query construido automáticamente:                                                               │
│   "paciente fumador 60 años tumor estadío II progresando radioterapia resistencia"             │
│                                                                                                 │
│ Pipeline RAG:                                                                                   │
│   1. BGE-M3 genera embedding (1024 dimensiones) → ~150 ms                                       │
│   2. ChromaDB busca similares (cosine similarity) → ~50 ms                                      │
│   3. Reranking por distancia → ~100 ms                                                          │
│                                                                                                 │
│ Resultados (3 documentos relevantes):                                                           │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │ Doc 1: "Resistencia a radioterapia en fumadores crónicos"                               │  │
│   │        Distancia: 0.12 | Fuente: guia_nccn_nsclc.pdf                                    │  │
│   ├─────────────────────────────────────────────────────────────────────────────────────────┤  │
│   │ Doc 2: "Hipoxia tumoral y efectividad de radiación ionizante"                           │  │
│   │        Distancia: 0.18 | Fuente: caso_maria_58.json                                     │  │
│   ├─────────────────────────────────────────────────────────────────────────────────────────┤  │
│   │ Doc 3: "Quimioterapia neoadyuvante para mejorar oxigenación tumoral"                    │  │
│   │        Distancia: 0.23 | Fuente: tratamientos_combinados.md                             │  │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                 │
│ Tiempo total RAG: ~400 ms                                                                       │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PASO 5: GENERACIÓN LLM                                                  [Vista Desarrollo]     │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ prompts.py construye prompt educativo:                                                          │
│                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │ [SYSTEM]                                                                                 │  │
│   │ Eres un profesor de oncología pulmonar. Explica conceptos médicos de forma              │  │
│   │ pedagógica a estudiantes de medicina. Basa tu respuesta en la evidencia proporcionada.  │  │
│   │                                                                                          │  │
│   │ [CONTEXTO RAG]                                                                           │  │
│   │ {documentos recuperados}                                                                 │  │
│   │                                                                                          │  │
│   │ [ESTADO ACTUAL]                                                                          │  │
│   │ Paciente de 60 años, fumador (35 pack-years), tumor estadío II, en radioterapia         │  │
│   │ desde hace 15 días, mostrando resistencia (células resistentes: 1.2 cm³)                 │  │
│   │                                                                                          │  │
│   │ [PREGUNTA IMPLÍCITA]                                                                     │  │
│   │ ¿Por qué el tumor no está respondiendo bien a la radioterapia?                          │  │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                 │
│ OllamaClient envía a llama3.2 → genera respuesta en ~5 segundos                                │
│                                                                                                 │
│ Componentes involucrados:                                                                       │
│   • app/rag/prompts.py → Template building                                                      │
│   • app/llm/ollama_client.py → HTTP async a Ollama                                              │
│   • Ollama container → llama3.2:7b inference                                                    │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PASO 6: RESPUESTA EDUCATIVA                                             [Vista Procesos]       │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ TeacherResponse generado:                                                                       │
│                                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│   │ {                                                                                        │  │
│   │   "explicacion": "La resistencia a radioterapia en fumadores crónicos se debe           │  │
│   │                   principalmente a la hipoxia tumoral. Las células con bajo oxígeno     │  │
│   │                   son 2-3 veces más resistentes a la radiación ionizante, ya que        │  │
│   │                   el oxígeno es necesario para generar los radicales libres que         │  │
│   │                   dañan el ADN tumoral...",                                              │  │
│   │                                                                                          │  │
│   │   "recomendacion": "Considera quimioterapia neoadyuvante con cisplatino para            │  │
│   │                     mejorar la oxigenación tumoral antes de retomar la radioterapia.    │  │
│   │                     También evalúa regímenes de radioterapia hiperfraccionada.",         │  │
│   │                                                                                          │  │
│   │   "fuentes": [                                                                           │  │
│   │     "guia_nccn_nsclc.pdf",                                                               │  │
│   │     "caso_maria_58.json",                                                                │  │
│   │     "tratamientos_combinados.md"                                                         │  │
│   │   ],                                                                                     │  │
│   │                                                                                          │  │
│   │   "advertencia": null,                                                                   │  │
│   │   "retrieved_chunks": 3,                                                                 │  │
│   │   "llm_model": "llama3.2:latest",                                                        │  │
│   │   "processing_time_ms": 5432                                                             │  │
│   │ }                                                                                        │  │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                 │
│ HTTP 200 OK → Unity recibe y deserializa                                                        │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ RESULTADO                                                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│ María lee la explicación en el panel 3D de VR y comprende:                                      │
│                                                                                                 │
│   1. ¿Por qué? → Hipoxia tumoral por daño pulmonar del tabaquismo                              │
│   2. ¿Qué hacer? → Quimioterapia neoadyuvante para mejorar oxigenación                         │
│   3. ¿Dónde profundizar? → Guías NCCN, casos similares                                         │
│                                                                                                 │
│ Métricas finales:                                                                               │
│   • Tiempo total E2E: ~6 segundos                                                               │
│   • Latencia de red: ~30 ms                                                                     │
│   • Tiempo RAG: ~400 ms                                                                         │
│   • Tiempo LLM: ~5 segundos                                                                     │
│                                                                                                 │
│ Valor educativo: ALTO                                                                           │
│   • Explicación contextualizada al caso específico                                              │
│   • Basada en evidencia médica (guías NCCN)                                                     │
│   • Recomendaciones accionables para el estudiante                                              │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Matriz de Trazabilidad: Casos de Uso → Vistas

| Caso de Uso | Vista Lógica | Vista Desarrollo | Vista Procesos | Vista Física |
|-------------|--------------|------------------|----------------|--------------|
| **UC-01** Simulación Libre | `TumorGrowthModel`, `RK4Solver`, `PatientProfile` | `CSharp_MathModel/Core/`, `Solvers/` | Solver loop RK4 | Quest 3 (local) |
| **UC-02** Cargar Caso | `SimulationState` | `loader.py`, `knowledge_base/` | HTTP GET, JSON parsing | ChromaDB, Backend |
| **UC-03** Consultar Profesor | `AITeacherService`, `TeacherResponse`, `LLMClient` | `app/services/`, `app/rag/`, `app/llm/` | Diagrama de secuencia completo | Quest→Backend→ChromaDB→Ollama |
| **UC-04** Ajustar Parámetros | `PatientProfile` (validadores) | `Models/PatientProfile.cs` | Validación síncrona | Quest 3 (local) |
| **UC-05** Visualizar Progresión | `SimulationHistory`, `LungState` | `Core/SimulationHistory.cs` | Render loop Unity | Quest 3 (local) |
| **UC-06** Buscar RAG | `MedicalKnowledgeRepository` | `app/repositories/`, `app/rag/` | Embedding + vector search | ChromaDB |

---

## 6. Requisitos No Funcionales Validados

| Escenario | RNF | Métrica Objetivo | Métrica Real |
|-----------|-----|------------------|--------------|
| UC-03 con timeout | **Latencia máxima** | < 15 s E2E | ~6 s típico |
| UC-03 con cache hit | **Latencia óptima** | < 100 ms | ~50 ms |
| UC-03 con ChromaDB caído | **Disponibilidad degradada** | Respuesta sin RAG | ✓ Fallback |
| UC-01 con 20 usuarios | **Concurrencia** | Sin degradación | Event loop async |
| UC-02 con 100 casos | **Escalabilidad RAG** | Búsqueda < 500 ms | HNSW O(log n) |
| UC-04 con valores inválidos | **Robustez** | Mensaje claro | Pydantic errors |

---

*Documento generado siguiendo el estándar 4+1 de Kruchten (IEEE Software, 1995)*
