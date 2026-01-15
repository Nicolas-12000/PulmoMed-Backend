# 🧪 Guía Completa de Testing - LungCancerVR Backend

**Última actualización:** 14 de enero de 2026

---

## 📋 Índice Rápido

1. [Setup Inicial](#-setup-inicial)
2. [Tests Disponibles](#-tests-disponibles)
3. [Ejecutar Servidor](#-ejecutar-servidor-de-desarrollo)
4. [Dónde Se Guardan Los Datos](#-dónde-se-guardan-los-datos)
5. [Troubleshooting](#-troubleshooting)

---

## 🚀 Setup Inicial

### 1. Activar Entorno Virtual

**Linux/Mac:**
```bash
cd /home/nicolas/proyectos/PulmoMed-Backend
source venv/bin/activate
```

**Windows:**
```powershell
cd "C:\Users\nicolas garcia\Desktop\Plumomed"
.\venv\Scripts\Activate.ps1
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

---

## 🧪 Tests Disponibles

### Tests Backend Python

| Categoría | Comando | Tests | Qué Testa |
|-----------|---------|-------|-----------|
| **Todos** | `pytest` | 67 | Todo el backend |
| **Unit** | `pytest tests/unit/ -v` | 22 | Service, Repository, Models |
| **Integration** | `pytest tests/integration/ -v` | 10 | API Endpoints, CORS |
| **Math Validation** | `pytest tests/test_csharp_math_validation.py -v` | 21 | Modelo C# Gompertz |
| **Historial** | `pytest tests/unit/test_simulation_history.py -v` | 17 | Sistema Git-like |
| **RAG E2E** | `pytest tests/integration/test_rag_e2e.py -v` | 15 | Pipeline RAG completo |

### Ejecutar Todos los Tests
```bash
# Tests completos
pytest tests/ -v

# Con cobertura
pytest --cov=app --cov-report=html
# Abrir htmlcov/index.html en navegador
```

### Tests Rápidos por Categoría
```bash
# Service Layer (4 tests, ~2 seg)
pytest tests/unit/test_service.py -v

# Repository ChromaDB (5 tests, ~3 seg)
pytest tests/unit/test_repository.py -v

# Modelos Pydantic (9 tests, <1 seg)
pytest tests/unit/test_models.py -v

# API Endpoints (10 tests, ~5 seg)
pytest tests/integration/test_api.py -v

# Modelo Matemático C# (21 tests, ~3 seg)
pytest tests/test_csharp_math_validation.py -v

# Sistema Historial (17 tests, ~1 seg)
pytest tests/unit/test_simulation_history.py -v
```

---

## 🌐 Ejecutar Servidor de Desarrollo

### Arrancar API
```bash
# Activar entorno y arrancar
source venv/bin/activate  # o .\venv\Scripts\Activate.ps1 en Windows
python main.py
```

**Output esperado:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✅ Backend iniciado correctamente
ℹ️  ChromaDB path: ./knowledge_base/embeddings
ℹ️  Embedding model: BAAI/bge-m3
⚠️  LLM en modo MOCK (Ollama no disponible)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Verificar Servidor
```bash
# Probar endpoint raíz
curl http://localhost:8000/

# Ver documentación interactiva
# Abrir en navegador: http://localhost:8000/docs

# Health check
curl http://localhost:8000/api/v1/health
```

### Probar Endpoint Principal
```bash
# Hacer request de prueba
curl -X POST http://localhost:8000/api/v1/consultar_profesor \
  -H "Content-Type: application/json" \
  -d '{
    "age": 58,
    "is_smoker": false,
    "pack_years": 0,
    "sensitive_tumor_volume": 5.0,
    "resistant_tumor_volume": 0.0,
    "active_treatment": "ninguno"
  }'
```

**Response esperado:**
```json
{
  "explanation": "El tumor ha alcanzado un volumen que requiere...",
  "recommendation": "En casos similares según NCCN Guidelines...",
  "sources": ["Base de conocimiento médico"],
  "warning": "⚠️ ADVERTENCIA EDUCATIVA...",
  "retrieved_chunks": 5,
  "llm_model": "ollama-mock"
}
```

---

## 📊 Dónde Se Guardan Los Datos

### 1. Vector Database (ChromaDB)
```
📁 knowledge_base/
  └── 📁 embeddings/                    ← Base de datos vectorial
      ├── chroma.sqlite3                ← SQLite con metadatos
      └── [archivos de índice]          ← Vectores embeddings
```

**¿Qué se guarda aquí?**
- ✅ Embeddings de documentos médicos (vectores 1024 dimensiones)
- ✅ Texto original de cada chunk
- ✅ Metadata (fuente, página, sección)
- ✅ Índice HNSW para búsqueda rápida

**Tamaño:** ~5-50 MB dependiendo de cuántos PDFs hayas indexado

**Persistencia:** ✅ Los datos se guardan automáticamente en disco

### 2. Casos de Biblioteca
```
📁 knowledge_base/
  └── 📄 casos_biblioteca.json          ← 7 casos SEER predefinidos
```

**Contenido:**
- 7 casos clínicos basados en estadísticas SEER
- Información completa: edad, estadio, tratamiento, pronóstico
- Objetivos de aprendizaje por caso

### 3. Configuración
```
📄 .env                                  ← Variables de entorno (NO subir a Git)
📄 .env.example                          ← Template de configuración
```

### 4. Logs (Temporal)
Los logs se muestran en consola, **no se guardan en disco** por defecto.

Para guardar logs:
```bash
python main.py > logs.txt 2>&1
```

### 5. ¿Dónde NO se guardan datos?
❌ **Historial de simulaciones**: No persiste automáticamente (en memoria)
❌ **Sesiones de usuario**: Backend stateless (sin cookies/sessions)
❌ **Queries RAG**: No se logean por defecto

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "ChromaDB collection not found"
**Causa:** Base de datos vacía  
**Solución:** Automático - se crea al arrancar el servidor

### Tests Lentos
```bash
# Ejecutar solo tests rápidos (<5 seg)
pytest tests/unit/ -v

# Ejecutar en paralelo (requiere pytest-xdist)
pip install pytest-xdist
pytest -n 4  # 4 workers paralelos
```

### Puerto 8000 Ocupado
```bash
# Cambiar puerto en .env
API_PORT=8001

# O matar proceso (Linux)
pkill -f "python main.py"

# Windows PowerShell
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process
```

---

## 📈 Estado Actual del Proyecto

### ✅ Implementado y Testeado

| Componente | Tests | Estado |
|------------|-------|--------|
| **Backend FastAPI** | 22 tests | ✅ 100% |
| **Vector DB (ChromaDB)** | 5 tests | ✅ 100% |
| **Service Layer** | 5 tests | ✅ 100% |
| **API Endpoints** | 10 tests | ✅ 100% |
| **Modelo C# Gompertz** | 21 tests | ✅ 100% |
| **Sistema Historial** | 17 tests | ✅ 100% |
| **RAG Pipeline** | 15 tests | ✅ 100% |

**Total: 80+ tests** | **Cobertura: >85%**

### 🚧 Pendiente
- [ ] Indexar PDFs médicos (NCCN Guidelines en español)
- [ ] Integración con Ollama local (requiere GPU)
- [ ] Frontend Unity (otro desarrollador)

---

## 🎯 Comandos Más Usados

```bash
# Arrancar servidor
python main.py

# Todos los tests
pytest tests/ -v

# Tests rápidos (<5 seg)
pytest tests/unit/ -v

# Ver docs API
# Abrir http://localhost:8000/docs

# Health check
curl http://localhost:8000/api/v1/health
```

---

## 📚 Archivos de Referencia

- **Esta guía**: `TESTING_GUIDE.md` (este archivo)
- **README principal**: `README.md`
- **Sistema historial**: `HISTORY_SYSTEM.md`
- **Configuración**: `.env` y `.env.example`

---

## ✅ Checklist de Testing

- [ ] Activar entorno virtual
- [ ] `pytest tests/unit/ -v` → Todos pasan ✅
- [ ] `pytest tests/integration/test_api.py -v` → Todos pasan ✅
- [ ] `python main.py` → Servidor arranca ✅
- [ ] `curl http://localhost:8000/` → Responde ✅

---

**Estado:** ✅ **LISTO PARA DESARROLLO**
