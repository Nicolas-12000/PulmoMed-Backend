# Vista Física - Modelo 4+1 de Kruchten

> **Propósito**: Describir la topología del sistema desde la perspectiva del ingeniero de sistemas: nodos de hardware, mapeo de software a hardware, y conexiones de red.
>
> **Audiencia**: Ingenieros de sistemas, DevOps, Administradores de infraestructura.
>
> **Diagramas UML**: Diagrama de Despliegue (Deployment Diagram).

---

## 1. Introducción

La Vista Física muestra cómo los componentes de software se mapean a la infraestructura de hardware. En PulmoMed, el sistema se despliega en un entorno de laboratorio universitario de realidad mixta:

| Entorno | Descripción |
|---------|-------------|
| **Clientes VR** | Meta Quest 3 (1-20 unidades) conectados vía WiFi |
| **Servidor Backend** | PC de alto rendimiento con GPU (opcional) |
| **Contenedores** | Docker Compose para orquestación de servicios |

Esta vista responde a la pregunta: *"¿Dónde se ejecuta el sistema?"*

---

## 2. Diagrama de Despliegue - Producción

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DIAGRAMA DE DESPLIEGUE UML                                          │
│                                    Entorno: Producción                                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              <<network>> LAN / WLAN Universitaria                            ║
    ║                                      (192.168.x.x)                                           ║
    ╠═════════════════════════════════════════════════════════════════════════════════════════════╣
    ║                                                                                              ║
    ║   ┌───────────────────────────────────────────────────────────────────────────────────────┐ ║
    ║   │  <<device>>                                                                            │ ║
    ║   │  Meta Quest 3 (Estudiante 1)                                                           │ ║
    ║   │                                                                                        │ ║
    ║   │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ ║
    ║   │  │  <<artifact>> PulmoMed.apk                                                        │ │ ║
    ║   │  │                                                                                   │ │ ║
    ║   │  │  ┌─────────────────────────┐  ┌─────────────────────────┐                        │ │ ║
    ║   │  │  │ <<component>>           │  │ <<component>>           │                        │ │ ║
    ║   │  │  │ Unity Runtime           │  │ C# MathModel            │                        │ │ ║
    ║   │  │  │ + XR Toolkit            │  │ (TumorGrowthModel)      │                        │ │ ║
    ║   │  │  │ + VR Renderer           │  │                         │                        │ │ ║
    ║   │  │  └─────────────────────────┘  └─────────────────────────┘                        │ │ ║
    ║   │  │                                                                                   │ │ ║
    ║   │  └──────────────────────────────────────────────────────────────────────────────────┘ │ ║
    ║   │                                                                                        │ ║
    ║   │  Hardware:                                                                             │ ║
    ║   │  • SoC: Snapdragon XR2 Gen 2                                                          │ ║
    ║   │  • RAM: 8 GB                                                                          │ ║
    ║   │  • WiFi: 6E (802.11ax)                                                                │ ║
    ║   │  • Storage: 128/256 GB                                                                │ ║
    ║   └───────────────────────────────────────────────────────────────────────────────────────┘ ║
    ║        │                                                                                     ║
    ║        │  HTTP/REST (JSON)                                                                   ║
    ║        │  Port 8000                                                                          ║
    ║        │                                                                                     ║
    ║        ▼                                                                                     ║
    ║   ┌───────────────────────────────────────────────────────────────────────────────────────┐ ║
    ║   │  <<execution environment>>                                                             │ ║
    ║   │  Backend Server (Linux / Windows)                                                      │ ║
    ║   │                                                                                        │ ║
    ║   │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ ║
    ║   │  │  <<container>> Docker Host                                                        │ │ ║
    ║   │  │                                                                                   │ │ ║
    ║   │  │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌───────────────────┐ │ │ ║
    ║   │  │  │ <<container>>           │  │ <<container>>           │  │ <<container>>     │ │ │ ║
    ║   │  │  │ pulmo-backend           │  │ chromadb                │  │ ollama            │ │ │ ║
    ║   │  │  │                         │  │                         │  │                   │ │ │ ║
    ║   │  │  │ ┌─────────────────────┐ │  │ ┌─────────────────────┐ │  │ ┌───────────────┐ │ │ │ ║
    ║   │  │  │ │ FastAPI + Uvicorn   │ │  │ │ ChromaDB Server     │ │  │ │ Ollama Server │ │ │ │ ║
    ║   │  │  │ │ Port: 8000          │ │  │ │ Port: 8001          │ │  │ │ Port: 11434   │ │ │ │ ║
    ║   │  │  │ │                     │ │  │ │                     │ │  │ │               │ │ │ │ ║
    ║   │  │  │ │ Python 3.11         │ │  │ │ HNSW Index          │ │  │ │ llama3.2:7b   │ │ │ │ ║
    ║   │  │  │ │ + dependencies      │ │  │ │ + embeddings        │ │  │ │               │ │ │ │ ║
    ║   │  │  │ └─────────────────────┘ │  │ └─────────────────────┘ │  │ └───────────────┘ │ │ │ ║
    ║   │  │  │                         │  │                         │  │                   │ │ │ ║
    ║   │  │  │ ENV:                    │  │ Volume:                 │  │ Volume:           │ │ │ ║
    ║   │  │  │ CHROMA_HOST=chromadb    │  │ ./chroma_data:/data     │  │ ./ollama:/root    │ │ │ ║
    ║   │  │  │ OLLAMA_HOST=ollama      │  │                         │  │                   │ │ │ ║
    ║   │  │  └─────────────────────────┘  └─────────────────────────┘  │ GPU: NVIDIA      │ │ │ ║
    ║   │  │                                                            │ (opcional)       │ │ │ ║
    ║   │  │                                                            └───────────────────┘ │ │ ║
    ║   │  │                                                                                   │ │ ║
    ║   │  │  ┌──────────────────────────────────────────────────────────────────────────────┐│ │ ║
    ║   │  │  │ <<library>> Sentence-Transformers (BGE-M3)                                   ││ │ ║
    ║   │  │  │ Loaded at startup, ~2GB memory                                               ││ │ ║
    ║   │  │  └──────────────────────────────────────────────────────────────────────────────┘│ │ ║
    ║   │  │                                                                                   │ │ ║
    ║   │  └──────────────────────────────────────────────────────────────────────────────────┘ │ ║
    ║   │                                                                                        │ ║
    ║   │  Hardware Mínimo:                         Hardware Recomendado:                       │ ║
    ║   │  • CPU: 4 cores                           • CPU: 8+ cores                             │ ║
    ║   │  • RAM: 16 GB                             • RAM: 32 GB                                │ ║
    ║   │  • Storage: 50 GB SSD                     • Storage: 100 GB NVMe                      │ ║
    ║   │  • GPU: Ninguna                           • GPU: NVIDIA RTX 3060+ (CUDA)              │ ║
    ║   └───────────────────────────────────────────────────────────────────────────────────────┘ ║
    ║                                                                                              ║
    ║   ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐║
    ║   │ <<device>>                │  │ <<device>>                │  │ <<device>>                │║
    ║   │ Meta Quest 3              │  │ Meta Quest 3              │  │ Meta Quest 3              │║
    ║   │ (Estudiante 2)            │  │ (Estudiante 3)            │  │ (Estudiante N)            │║
    ║   │ ┌───────────────────────┐ │  │ ┌───────────────────────┐ │  │ ┌───────────────────────┐ │║
    ║   │ │ PulmoMed.apk          │ │  │ │ PulmoMed.apk          │ │  │ │ PulmoMed.apk          │ │║
    ║   │ └───────────────────────┘ │  │ └───────────────────────┘ │  │ └───────────────────────┘ │║
    ║   └───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘║
    ║                                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Diagrama de Despliegue - Docker Compose

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DIAGRAMA DE DESPLIEGUE UML                                          │
│                                    Entorno: Docker Compose                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
    ║  <<execution environment>> Docker Host (Linux/Windows with Docker Desktop)                   ║
    ╠═════════════════════════════════════════════════════════════════════════════════════════════╣
    ║                                                                                              ║
    ║   ┌─────────────────────────────────────────────────────────────────────────────────────┐   ║
    ║   │  <<network>> pulmo-network (bridge)                                                  │   ║
    ║   │                                                                                      │   ║
    ║   │  ┌─────────────────────────┐   ┌─────────────────────────┐   ┌───────────────────┐  │   ║
    ║   │  │ <<container>>           │   │ <<container>>           │   │ <<container>>     │  │   ║
    ║   │  │ pulmo-backend           │   │ chromadb                │   │ ollama            │  │   ║
    ║   │  ├─────────────────────────┤   ├─────────────────────────┤   ├───────────────────┤  │   ║
    ║   │  │ Image:                  │   │ Image:                  │   │ Image:            │  │   ║
    ║   │  │ pulmo-backend:latest    │   │ chromadb/chroma:latest  │   │ ollama/ollama     │  │   ║
    ║   │  │                         │   │                         │   │                   │  │   ║
    ║   │  │ Ports:                  │   │ Ports:                  │   │ Ports:            │  │   ║
    ║   │  │ 8000:8000 ◀─────────────┼───┼───── External Access    │   │ 11434:11434       │  │   ║
    ║   │  │                         │   │ 8001:8000               │   │                   │  │   ║
    ║   │  │ Environment:            │   │                         │   │ GPU Access:       │  │   ║
    ║   │  │ CHROMA_HOST=chromadb    │   │ Volumes:                │   │ nvidia (optional) │  │   ║
    ║   │  │ OLLAMA_HOST=ollama      │   │ chroma_data:/chroma     │   │                   │  │   ║
    ║   │  │                         │   │                         │   │ Volumes:          │  │   ║
    ║   │  │ Depends On:             │   │                         │   │ ollama_models:    │  │   ║
    ║   │  │ - chromadb              │   │                         │   │ /root/.ollama     │  │   ║
    ║   │  │ - ollama                │   │                         │   │                   │  │   ║
    ║   │  └───────────┬─────────────┘   └────────────┬────────────┘   └─────────┬─────────┘  │   ║
    ║   │              │                              │                          │            │   ║
    ║   │              │  chromadb:8000               │      ollama:11434        │            │   ║
    ║   │              └──────────────────────────────┴──────────────────────────┘            │   ║
    ║   │                                                                                      │   ║
    ║   └─────────────────────────────────────────────────────────────────────────────────────┘   ║
    ║                                                                                              ║
    ║   ┌─────────────────────────────────────────────────────────────────────────────────────┐   ║
    ║   │  <<volume>> Persistent Storage                                                       │   ║
    ║   │                                                                                      │   ║
    ║   │  • chroma_data/        → Vector store (embeddings, ~500MB-2GB)                      │   ║
    ║   │  • ollama_models/      → LLM models (~4-8 GB per model)                             │   ║
    ║   │  • knowledge_base/     → JSON source files (mounted read-only)                      │   ║
    ║   │                                                                                      │   ║
    ║   └─────────────────────────────────────────────────────────────────────────────────────┘   ║
    ║                                                                                              ║
    ║   Acceso Externo:                                                                            ║
    ║   • 0.0.0.0:8000 → pulmo-backend (Unity clients)                                            ║
    ║   • 0.0.0.0:11434 → ollama (optional: direct testing)                                       ║
    ║                                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Especificación de Nodos

| Nodo | Tipo | Hardware Mínimo | Software | Responsabilidad |
|------|------|-----------------|----------|-----------------|
| **Meta Quest 3** | VR Headset | Snapdragon XR2 Gen 2, 8GB RAM | Android 12+, Unity 2022.3 | Cliente VR, simulación matemática local, renderizado 3D |
| **Backend Server** | Servidor físico/VM | 4 CPU, 16GB RAM, 50GB SSD | Ubuntu 22.04, Docker | API REST, RAG, orquestación LLM |
| **pulmo-backend** | Container | 2 CPU, 4GB RAM | Python 3.11, FastAPI | Endpoints REST, lógica de negocio |
| **chromadb** | Container | 1 CPU, 2GB RAM, 10GB SSD | chromadb/chroma:latest | Almacenamiento vectorial, búsqueda semántica |
| **ollama** | Container | 4 CPU, 8GB RAM | ollama/ollama:latest | Inferencia LLM local |

---

## 5. Conexiones de Red

| Origen | Destino | Protocolo | Puerto | Datos | Latencia Esperada |
|--------|---------|-----------|--------|-------|-------------------|
| Quest 3 | Backend | HTTP/1.1 | 8000 | JSON (~2-5 KB) | < 50 ms |
| Backend | ChromaDB | HTTP/1.1 | 8001 | Vectors (~10 KB) | < 10 ms |
| Backend | Ollama | HTTP/1.1 | 11434 | Prompts (~5-20 KB) | < 5 ms |
| Backend | Embeddings | In-process | N/A | Tensors | < 1 ms |

---

## 6. Docker Compose (Referencia)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    container_name: pulmo-backend
    ports:
      - "8000:8000"
    environment:
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - OLLAMA_BASE_URL=http://ollama:11434
      - MODEL_NAME=llama3.2
    depends_on:
      chromadb:
        condition: service_started
      ollama:
        condition: service_started
    volumes:
      - ./knowledge_base:/app/knowledge_base:ro
    networks:
      - pulmo-network
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    networks:
      - pulmo-network
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - pulmo-network
    restart: unless-stopped

networks:
  pulmo-network:
    driver: bridge

volumes:
  chroma_data:
    name: pulmo_chroma_data
  ollama_models:
    name: pulmo_ollama_models
```

---

## 7. Requisitos No Funcionales de Despliegue

| Atributo | Requisito | Táctica | Métrica |
|----------|-----------|---------|---------|
| **Latencia** | Respuesta rápida para VR | Red local, async I/O | < 100ms Quest→Backend |
| **Ancho de Banda** | Soportar múltiples clientes | JSON compacto (~5KB) | 1 Mbps mínimo por cliente |
| **Disponibilidad** | Best-effort (no HA) | Restart policies, healthchecks | 99% uptime en horario lab |
| **Escalabilidad** | 1-20 usuarios concurrentes | Event loop async, connection pooling | Sin degradación hasta 20 |
| **Seguridad** | Red local aislada | Firewall, no exponer Ollama | Solo puerto 8000 público |
| **Backup** | Preservar conocimiento | Volumen persistente, backup diario | knowledge_base versionado |
| **Monitoreo** | Observabilidad | Docker logs, healthcheck endpoint | Logs a stdout, /health |

---

## 8. Procedimiento de Despliegue

### Prerrequisitos

```bash
# Verificar Docker y Docker Compose
docker --version          # >= 24.0
docker compose version    # >= 2.20

# Verificar GPU (opcional)
nvidia-smi                # NVIDIA driver >= 525
```

### Despliegue

```bash
# 1. Clonar repositorio
git clone https://github.com/org/PulmoMed-Backend.git
cd PulmoMed-Backend

# 2. Configurar variables de entorno
cp .env.example .env
nano .env  # Ajustar configuración

# 3. Construir y levantar servicios
docker compose up -d --build

# 4. Verificar estado
docker compose ps
docker compose logs -f backend

# 5. Descargar modelo LLM (primera vez)
docker exec ollama ollama pull llama3.2

# 6. Verificar salud del sistema
curl http://localhost:8000/health
```

### Verificación

```bash
# Healthcheck completo
curl -s http://localhost:8000/health | jq

# Respuesta esperada:
{
  "status": "ok",
  "llm_available": true,
  "chroma_available": true,
  "model_loaded": true,
  "knowledge_docs": 42
}
```

---

*Documento generado siguiendo el estándar 4+1 de Kruchten (IEEE Software, 1995)*
