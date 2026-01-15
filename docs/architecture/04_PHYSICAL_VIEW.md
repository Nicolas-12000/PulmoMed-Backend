# Vista Física - Modelo 4+1

## Descripción General

La Vista Física describe el mapeo del software a hardware, mostrando cómo los componentes se despliegan en la infraestructura física y cómo se comunican a través de la red.

---

## Diagrama de Despliegue General

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DEPLOYMENT OVERVIEW                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

      ┌────────────────────┐                              ┌────────────────────────────────┐
      │  <<device>>        │                              │  <<execution environment>>     │
      │  VR Headset        │                              │  University Server / Cloud     │
      │  (Meta Quest 3)    │                              │                                │
      ├────────────────────┤                              │  ┌──────────────────────────┐ │
      │                    │                              │  │  <<container>>           │ │
      │  ┌──────────────┐  │                              │  │  pulmomed-backend        │ │
      │  │ <<artifact>> │  │      HTTP/REST               │  │  (Docker)                │ │
      │  │ Unity App    │  │      Port 8000               │  ├──────────────────────────┤ │
      │  │ (.apk)       │──┼──────────────────────────────┼─▶│ ┌────────────────────┐  │ │
      │  │              │  │                              │  │ │ <<artifact>>       │  │ │
      │  │ • VR Runtime │  │                              │  │ │ FastAPI App        │  │ │
      │  │ • Math Model │  │                              │  │ │ main.py            │  │ │
      │  │ • HTTP Client│  │                              │  │ └────────────────────┘  │ │
      │  └──────────────┘  │                              │  │ ┌────────────────────┐  │ │
      │                    │                              │  │ │ <<artifact>>       │  │ │
      └────────────────────┘                              │  │ │ BGE-M3 Embeddings  │  │ │
                                                          │  │ │ (HuggingFace)      │  │ │
      ┌────────────────────┐                              │  │ └────────────────────┘  │ │
      │  <<device>>        │                              │  └───────────┬──────────────┘ │
      │  Desktop/Laptop    │                              │              │                │
      │  (Professor)       │                              │              │ Port 8001      │
      ├────────────────────┤                              │              ▼                │
      │  ┌──────────────┐  │      HTTP                    │  ┌──────────────────────────┐ │
      │  │ <<artifact>> │  │      Port 8000               │  │  <<container>>           │ │
      │  │ Web Browser  │──┼──────────────────────────────┼─▶│  chromadb                │ │
      │  │              │  │                              │  │  (Docker)                │ │
      │  └──────────────┘  │                              │  ├──────────────────────────┤ │
      │                    │                              │  │ ┌────────────────────┐  │ │
      └────────────────────┘                              │  │ │ <<artifact>>       │  │ │
                                                          │  │ │ Vector Database    │  │ │
                                                          │  │ │ Collection:        │  │ │
                                                          │  │ │ medical_knowledge  │  │ │
                                                          │  │ └────────────────────┘  │ │
                                                          │  └───────────┬──────────────┘ │
                                                          │              │                │
                                                          │              │ Port 11434     │
                                                          │              ▼                │
                                                          │  ┌──────────────────────────┐ │
                                                          │  │  <<container>>           │ │
                                                          │  │  ollama                  │ │
                                                          │  │  (Docker / Native)       │ │
                                                          │  ├──────────────────────────┤ │
                                                          │  │ ┌────────────────────┐  │ │
                                                          │  │ │ <<artifact>>       │  │ │
                                                          │  │ │ LLM Model          │  │ │
                                                          │  │ │ llama3.2:3b /      │  │ │
                                                          │  │ │ mistral:7b         │  │ │
                                                          │  │ └────────────────────┘  │ │
                                                          │  └──────────────────────────┘ │
                                                          │                                │
                                                          └────────────────────────────────┘
```

---

## Diagrama Docker Compose

```yaml
# docker-compose.yml (especificación)
version: '3.8'

services:
  # ╔══════════════════════════════════════════════════════════════════╗
  # ║                     BACKEND CONTAINER                            ║
  # ╚══════════════════════════════════════════════════════════════════╝
  pulmomed-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8001
    volumes:
      - ./knowledge_base:/app/knowledge_base
    depends_on:
      - chromadb
      - ollama
    networks:
      - pulmomed-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ╔══════════════════════════════════════════════════════════════════╗
  # ║                     CHROMADB CONTAINER                           ║
  # ╚══════════════════════════════════════════════════════════════════╝
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    networks:
      - pulmomed-network

  # ╔══════════════════════════════════════════════════════════════════╗
  # ║                     OLLAMA CONTAINER                             ║
  # ╚══════════════════════════════════════════════════════════════════╝
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - pulmomed-network

volumes:
  chroma_data:
  ollama_data:

networks:
  pulmomed-network:
    driver: bridge
```

---

## Diagrama de Red Detallado

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              NETWORK TOPOLOGY                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│                           Internet / University LAN                                      │
│     ════════════════════════════════════════════════════════════════════════            │
│                    │                                    │                                │
│                    │                                    │                                │
│     ┌──────────────┴───────────────┐    ┌──────────────┴───────────────┐               │
│     │       VR Lab Network         │    │     Professor Network        │               │
│     │       (172.16.0.0/24)        │    │     (172.16.1.0/24)          │               │
│     └──────────────┬───────────────┘    └──────────────┬───────────────┘               │
│                    │                                    │                                │
│     ┌──────────────┼──────────────┐                    │                                │
│     │              │              │                    │                                │
│     ▼              ▼              ▼                    ▼                                │
│  ┌──────┐     ┌──────┐     ┌──────┐             ┌──────────┐                           │
│  │Quest │     │Quest │     │Quest │             │ Browser  │                           │
│  │  1   │     │  2   │     │  N   │             │ (Admin)  │                           │
│  └──┬───┘     └──┬───┘     └──┬───┘             └────┬─────┘                           │
│     │            │            │                      │                                  │
│     └────────────┴────────────┴──────────────────────┘                                  │
│                              │                                                          │
│                              │ HTTPS (Future) / HTTP                                    │
│                              │ Port 8000                                                │
│                              ▼                                                          │
│     ╔════════════════════════════════════════════════════════════════════════╗         │
│     ║                     Docker Network: pulmomed-network                    ║         │
│     ║                     (172.20.0.0/16) - Bridge Mode                       ║         │
│     ╠════════════════════════════════════════════════════════════════════════╣         │
│     ║                                                                         ║         │
│     ║   ┌─────────────────────────────────────────────────────────────────┐  ║         │
│     ║   │                pulmomed-backend (172.20.0.2)                    │  ║         │
│     ║   │                                                                  │  ║         │
│     ║   │    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐         │  ║         │
│     ║   │    │  FastAPI    │   │  Embedding  │   │   httpx     │         │  ║         │
│     ║   │    │  :8000      │   │  Model      │   │   Client    │         │  ║         │
│     ║   │    └─────────────┘   └─────────────┘   └──────┬──────┘         │  ║         │
│     ║   │                                               │                 │  ║         │
│     ║   └───────────────────────────────────────────────┼─────────────────┘  ║         │
│     ║                     │                             │                    ║         │
│     ║                     │ chromadb://172.20.0.3:8000  │                    ║         │
│     ║                     │                             │                    ║         │
│     ║                     ▼                             │                    ║         │
│     ║   ┌─────────────────────────────────┐            │                    ║         │
│     ║   │      chromadb (172.20.0.3)      │            │                    ║         │
│     ║   │                                  │            │                    ║         │
│     ║   │    ┌─────────────────────────┐  │            │                    ║         │
│     ║   │    │  ChromaDB Server        │  │            │                    ║         │
│     ║   │    │  :8000 (internal)       │  │            │                    ║         │
│     ║   │    │  :8001 (external)       │  │            │                    ║         │
│     ║   │    └─────────────────────────┘  │            │                    ║         │
│     ║   │    ┌─────────────────────────┐  │            │                    ║         │
│     ║   │    │  Volume: chroma_data    │  │            │                    ║         │
│     ║   │    │  /chroma/chroma         │  │            │                    ║         │
│     ║   │    └─────────────────────────┘  │            │                    ║         │
│     ║   └─────────────────────────────────┘            │                    ║         │
│     ║                                                  │                    ║         │
│     ║                          http://172.20.0.4:11434 │                    ║         │
│     ║                                                  ▼                    ║         │
│     ║   ┌─────────────────────────────────────────────────────────────────┐ ║         │
│     ║   │                    ollama (172.20.0.4)                          │ ║         │
│     ║   │                                                                  │ ║         │
│     ║   │    ┌─────────────────────────┐   ┌─────────────────────────┐   │ ║         │
│     ║   │    │  Ollama Server          │   │  GPU Access             │   │ ║         │
│     ║   │    │  :11434                 │   │  (NVIDIA Runtime)       │   │ ║         │
│     ║   │    └─────────────────────────┘   └─────────────────────────┘   │ ║         │
│     ║   │    ┌─────────────────────────┐                                  │ ║         │
│     ║   │    │  Volume: ollama_data    │   Models: llama3.2, mistral     │ ║         │
│     ║   │    │  /root/.ollama          │                                  │ ║         │
│     ║   │    └─────────────────────────┘                                  │ ║         │
│     ║   └─────────────────────────────────────────────────────────────────┘ ║         │
│     ║                                                                         ║         │
│     ╚════════════════════════════════════════════════════════════════════════╝         │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuración de Nodos

### Nodo: pulmomed-backend

| Especificación | Valor Recomendado |
|----------------|-------------------|
| **CPU** | 4 cores |
| **RAM** | 8 GB (4GB para embeddings) |
| **Disco** | 10 GB SSD |
| **OS** | Ubuntu 22.04 / Alpine |
| **Runtime** | Python 3.11+ |
| **Puertos** | 8000 (HTTP) |

### Nodo: chromadb

| Especificación | Valor Recomendado |
|----------------|-------------------|
| **CPU** | 2 cores |
| **RAM** | 4 GB |
| **Disco** | 20 GB SSD (para índices) |
| **Puertos** | 8000 (interno), 8001 (externo) |
| **Volumen** | chroma_data:/chroma/chroma |

### Nodo: ollama

| Especificación | Valor Recomendado |
|----------------|-------------------|
| **CPU** | 8 cores |
| **RAM** | 16 GB (para modelos 7B) |
| **GPU** | NVIDIA RTX 3060+ (12GB VRAM) |
| **Disco** | 50 GB (para modelos) |
| **Puertos** | 11434 |
| **Volumen** | ollama_data:/root/.ollama |

### Nodo: Unity VR Client (Quest 3)

| Especificación | Valor |
|----------------|-------|
| **Procesador** | Snapdragon XR2 Gen 2 |
| **RAM** | 8 GB |
| **Storage** | Variable (512GB max) |
| **Conectividad** | WiFi 6E |
| **Latency Req** | < 100ms (network) |

---

## Escenarios de Despliegue

### Escenario 1: Desarrollo Local

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESARROLLO LOCAL                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 Máquina del Desarrollador                │   │
│   │                                                          │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐        │   │
│   │   │ uvicorn   │   │ ChromaDB  │   │ Ollama    │        │   │
│   │   │ :8000     │   │ :8001     │   │ :11434    │        │   │
│   │   │           │   │ (Docker)  │   │ (native)  │        │   │
│   │   └───────────┘   └───────────┘   └───────────┘        │   │
│   │                                                          │   │
│   │   Commands:                                              │   │
│   │   $ uvicorn main:app --reload                           │   │
│   │   $ docker run -p 8001:8000 chromadb/chroma             │   │
│   │   $ ollama serve                                         │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 Unity Editor (Testing)                   │   │
│   │                                                          │   │
│   │   BackendClient.BASE_URL = "http://localhost:8000"      │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Escenario 2: Universidad (Multi-usuario)

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIVERSIDAD (PRODUCCIÓN)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌───────────────────────────────────────────┐                 │
│   │           Servidor Principal               │                 │
│   │           (Dell PowerEdge / Cloud VM)      │                 │
│   │                                            │                 │
│   │   ┌────────────────────────────────────┐  │                 │
│   │   │     Docker Compose Stack            │  │                 │
│   │   │                                     │  │                 │
│   │   │   ┌─────────┐  ┌─────────┐         │  │                 │
│   │   │   │backend  │  │chromadb │         │  │                 │
│   │   │   │ x2      │  │         │         │  │                 │
│   │   │   │(replicas)│ │         │         │  │                 │
│   │   │   └─────────┘  └─────────┘         │  │                 │
│   │   │                                     │  │                 │
│   │   │   ┌─────────┐  ┌─────────┐         │  │                 │
│   │   │   │ nginx   │  │ ollama  │         │  │                 │
│   │   │   │(L.B.)   │  │ (GPU)   │         │  │                 │
│   │   │   └─────────┘  └─────────┘         │  │                 │
│   │   │                                     │  │                 │
│   │   └────────────────────────────────────┘  │                 │
│   │                                            │                 │
│   │   IP: 192.168.1.100                        │                 │
│   │   DNS: pulmomed.med.university.edu         │                 │
│   │                                            │                 │
│   └───────────────────────────────────────────┘                 │
│                         │                                        │
│                         │ WiFi 6E                                │
│                         ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 VR Laboratory                            │   │
│   │                                                          │   │
│   │   [Quest 3] [Quest 3] [Quest 3] ... [Quest 3]           │   │
│   │      #1        #2        #3           #20               │   │
│   │                                                          │   │
│   │   Concurrent Users: Up to 20                            │   │
│   │   Session Length: ~30 min avg                           │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Escenario 3: Cloud (Escalable)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD DEPLOYMENT (AWS/GCP)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                     Load Balancer                         │  │
│   │                  (ALB / Cloud Load Balancer)              │  │
│   │                     pulmomed.example.com                  │  │
│   └────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│            ┌───────────────┼───────────────┐                    │
│            ▼               ▼               ▼                    │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│   │ backend-1    │ │ backend-2    │ │ backend-N    │           │
│   │ (ECS/GKE)    │ │ (ECS/GKE)    │ │ (ECS/GKE)    │           │
│   │              │ │              │ │              │           │
│   │ Auto-scaling │ │ Auto-scaling │ │ Auto-scaling │           │
│   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘           │
│          │                │                │                    │
│          └────────────────┼────────────────┘                    │
│                           │                                     │
│            ┌──────────────┴──────────────┐                     │
│            ▼                             ▼                     │
│   ┌──────────────────┐        ┌──────────────────┐            │
│   │   ChromaDB       │        │   Ollama         │            │
│   │   (Managed)      │        │   (GPU Instance) │            │
│   │                  │        │                  │            │
│   │   or Pinecone/   │        │   g4dn.xlarge    │            │
│   │   Weaviate       │        │   (AWS)          │            │
│   └──────────────────┘        └──────────────────┘            │
│                                                                  │
│   Estimated Cost: $200-500/month (light usage)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requisitos de Hardware Mínimos

### Backend Server (Producción)

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| GPU | - | NVIDIA RTX 3070+ |
| Storage | 100 GB SSD | 250 GB NVMe |
| Network | 100 Mbps | 1 Gbps |

### Para 20 usuarios concurrentes:
- Backend: 8 cores, 16 GB RAM
- Ollama: Dedicated GPU (12+ GB VRAM)
- ChromaDB: 8 GB RAM, 50 GB SSD

---

## Herramientas para Diagramas

- **Draw.io** con plantillas de deployment UML
- **AWS Architecture Icons** para cloud
- **Docker icons** oficiales para contenedores
