# Documentación de Arquitectura - PulmoMed VR

## Modelo 4+1 de Kruchten

Esta carpeta contiene la documentación arquitectónica del sistema PulmoMed siguiendo el **Modelo 4+1** de Philippe Kruchten.

---

## 📚 Índice de Vistas

| Vista | Archivo | Descripción |
|-------|---------|-------------|
| **Lógica** | [01_LOGICAL_VIEW.md](01_LOGICAL_VIEW.md) | Clases, interfaces y relaciones entre componentes |
| **Desarrollo** | [02_DEVELOPMENT_VIEW.md](02_DEVELOPMENT_VIEW.md) | Organización del código, módulos y capas |
| **Procesos** | [03_PROCESS_VIEW.md](03_PROCESS_VIEW.md) | Flujos de ejecución, secuencias y concurrencia |
| **Física** | [04_PHYSICAL_VIEW.md](04_PHYSICAL_VIEW.md) | Despliegue, infraestructura y Docker |
| **Escenarios (+1)** | [05_SCENARIOS_VIEW.md](05_SCENARIOS_VIEW.md) | Casos de uso y validación de arquitectura |

---

## 🎯 Propósito

Estos documentos sirven como **especificaciones detalladas** para generar diagramas profesionales usando herramientas como:

- **PlantUML** - Diagramas de clases, secuencia, actividad
- **Draw.io** - Diagramas de despliegue, componentes
- **Lucidchart** - Diagramas de arquitectura cloud
- **Mermaid** - Diagramas embebidos en Markdown

---

## 🏗️ Resumen de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     PULMOMED VR ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐              ┌─────────────────────────┐  │
│   │  Unity VR App   │    HTTP      │     Python Backend      │  │
│   │                 │◀────────────▶│                         │  │
│   │  • Math Model   │   REST API   │  • FastAPI              │  │
│   │  • 3D Render    │   Port 8000  │  • RAG Pipeline         │  │
│   │  • User Input   │              │  • LLM Integration      │  │
│   └─────────────────┘              └────────────┬────────────┘  │
│                                                 │               │
│                                    ┌────────────┴────────────┐  │
│                                    │                         │  │
│                               ┌────▼────┐            ┌───────▼──┐
│                               │ChromaDB │            │ Ollama   │
│                               │(Vectors)│            │ (LLM)    │
│                               └─────────┘            └──────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Tecnologías Principales

### Backend (Python)
- **FastAPI** 0.109.0 - REST API async
- **ChromaDB** 0.4.22 - Vector database
- **BGE-M3** - Multilingual embeddings
- **Ollama** - Local LLM server

### Cliente (Unity C#)
- **Unity** 2022.3 LTS - Game engine
- **XR Interaction Toolkit** - VR support
- **Newtonsoft.Json** - Serialization

### Infraestructura
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

---

## 🚀 Cómo usar esta documentación

1. **Revisión de arquitectura**: Leer las vistas para entender el sistema
2. **Generar diagramas**: Usar los diagramas ASCII como especificación para herramientas profesionales
3. **Onboarding**: Guiar a nuevos desarrolladores con la estructura del código
4. **Decisiones técnicas**: Documentar cambios arquitectónicos futuros

---

## 📅 Última actualización

**Versión**: 2.1.0  
**Fecha**: Julio 2025  
**Autor**: Equipo PulmoMed
