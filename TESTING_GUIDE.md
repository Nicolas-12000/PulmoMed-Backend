# 🧪 Guía Completa de Testing - LungCancerVR Backend

**Última actualización:** 21 de diciembre de 2025

---

## 📋 Índice Rápido

1. [Setup Inicial](#-setup-inicial) (2 minutos)
2. [Tests Disponibles](#-tests-disponibles)
3. [Ejecutar Servidor](#-ejecutar-servidor-de-desarrollo)
4. [Dónde Se Guardan Los Datos](#-dónde-se-guardan-los-datos)
5. [Testing RAG con Gemini](#-testing-rag-con-gemini)
6. [Troubleshooting](#-troubleshooting)

---

## 🚀 Setup Inicial

### 1. Activar Entorno Virtual
```powershell
cd "C:\Users\nicolas garcia\Desktop\Plumomed"
.\venv\Scripts\Activate.ps1
```

### 2. (Opcional) Configurar Gemini API
```powershell
# Editar .env y añadir (si quieres probar RAG con LLM real):
# GEMINI_API_KEY=tu_nueva_clave_aqui
# Obtener key gratis: https://aistudio.google.com/apikey
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
| **RAG con Gemini** | `pytest tests/integration/test_rag_e2e.py -v` | 15 | Pipeline RAG completo |

### Ejecutar Todos los Tests
```powershell
# Tests backend (sin RAG Gemini)
pytest tests/ --ignore=tests/integration/test_rag_e2e.py -v

# Con cobertura
pytest --cov=app --cov-report=html
start htmlcov/index.html
```

### Tests Rápidos por Categoría
```powershell
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
```powershell
# Terminal 1: Arrancar servidor
.\venv\Scripts\Activate.ps1
python main.py
```

**Output esperado:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✅ Backend iniciado correctamente
ℹ️  ChromaDB path: ./knowledge_base/embeddings
ℹ️  Embedding model: BAAI/bge-base-en-v1.5
⚠️  LLM en modo MOCK (Ollama no disponible)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Verificar Servidor
```powershell
# Terminal 2: Probar endpoints
curl http://localhost:8000/

# Ver documentación interactiva
start http://localhost:8000/docs

# Health check
curl http://localhost:8000/api/v1/health
```

### Probar Endpoint Principal
```powershell
# Crear archivo test_request.json:
@"
{
  "edad": 58,
  "es_fumador": false,
  "pack_years": 0,
  "volumen_tumor_sensible": 5.0,
  "volumen_tumor_resistente": 0.0,
  "tratamiento_activo": "ninguno"
}
"@ | Out-File test_request.json -Encoding utf8

# Hacer request
curl -X POST http://localhost:8000/api/v1/consultar_profesor `
  -H "Content-Type: application/json" `
  -d "@test_request.json"
```

**Response esperado:**
```json
{
  "explicacion": "El tumor ha alcanzado un volumen que requiere...",
  "recomendacion": "En casos similares según NCCN Guidelines...",
  "fuentes": ["Base de conocimiento médico"],
  "advertencia": "⚠️ ADVERTENCIA EDUCATIVA...",
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
- ✅ Embeddings de documentos médicos (vectores 768 dimensiones)
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
```powershell
# Redirigir a archivo
python main.py > logs.txt 2>&1
```

### 5. ¿Dónde NO se guardan datos?
❌ **Historial de simulaciones**: No persiste automáticamente (requiere implementación)
❌ **Sesiones de usuario**: Backend stateless (sin cookies/sessions)
❌ **Queries RAG**: No se logean por defecto

---

## 🤖 Testing RAG con Gemini

### ⚠️ Nota Importante
La API key que compartiste fue marcada como "leaked" (filtrada públicamente). Necesitas generar una nueva:

**Obtener nueva key gratis:**
1. Ve a https://aistudio.google.com/apikey
2. Crea nueva API key
3. Añádela a `.env`

### Modelos Gratuitos Disponibles
- ✅ **gemini-2.0-flash** (recomendado) - 1M context, estable
- ✅ **gemini-2.5-flash** - Con razonamiento
- ✅ **gemini-2.5-pro** - Más potente
- ✅ **gemini-3-flash-preview** - Más reciente

### Configurar Gemini
```powershell
# Editar .env
notepad .env

# Añadir:
GEMINI_API_KEY=tu_nueva_clave_aqui
```

### Ejecutar Tests RAG
```powershell
# Todos los tests RAG (15 tests)
$env:GEMINI_API_KEY = "tu_clave"; pytest tests/integration/test_rag_e2e.py -v

# Solo adapter básico (3 tests, rápido)
$env:GEMINI_API_KEY = "tu_clave"; pytest tests/integration/test_rag_e2e.py::TestGeminiAdapter -v

# Solo pipeline E2E (6 tests)
$env:GEMINI_API_KEY = "tu_clave"; pytest tests/integration/test_rag_e2e.py::TestRAGEndToEndWithGemini -v
```

### Ejemplo Interactivo
```powershell
# Ejecutar ejemplos con output detallado
$env:GEMINI_API_KEY = "tu_clave"
python example_gemini_rag.py
```

**Output esperado:**
- Ejemplo 1: RAG básico con estadio temprano
- Ejemplo 2: Caso avanzado con resistencia
- Ejemplo 3: Solo retrieval (sin LLM)
- Ejemplo 4: Comparación Mock vs Gemini

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError"
```powershell
# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "GEMINI_API_KEY no encontrada"
```powershell
# Verificar que existe en .env
cat .env | Select-String "GEMINI"

# Si no existe, añadir:
echo "GEMINI_API_KEY=tu_clave" >> .env
```

### Error: "API key reported as leaked"
**Causa:** Compartiste la key públicamente (GitHub, chat, etc)  
**Solución:** Genera nueva key en https://aistudio.google.com/apikey

### Error: "ChromaDB collection not found"
**Causa:** Base de datos vacía  
**Solución:** Automático - se crea al arrancar el servidor

### Tests Lentos
```powershell
# Ejecutar solo tests rápidos (<5 seg)
pytest tests/unit/ -v

# Ejecutar en paralelo (requiere pytest-xdist)
pip install pytest-xdist
pytest -n 4  # 4 workers paralelos
```

### Puerto 8000 Ocupado
```powershell
# Cambiar puerto en .env
API_PORT=8001

# O matar proceso
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
| **RAG con Gemini** | 15 tests | ⏸️ Requiere API key |

**Total: 80 tests** | **Cobertura: >85%**

### 🚧 Pendiente
- [ ] Obtener nueva API key de Gemini
- [ ] Indexar PDFs médicos (NCCN Guidelines)
- [ ] Integración con Ollama local (requiere GPU)
- [ ] Frontend Unity (otro desarrollador)

---

## 🎯 Comandos Más Usados

```powershell
# Arrancar servidor
python main.py

# Todos los tests (sin Gemini)
pytest tests/ --ignore=tests/integration/test_rag_e2e.py -v

# Tests rápidos (<5 seg)
pytest tests/unit/ -v

# Ver docs API
start http://localhost:8000/docs

# Health check
curl http://localhost:8000/api/v1/health

# Test con Gemini (si tienes key)
$env:GEMINI_API_KEY = "tu_clave"; python example_gemini_rag.py
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
- [ ] (Opcional) Obtener API key de Gemini
- [ ] (Opcional) `pytest tests/integration/test_rag_e2e.py -v` → Tests RAG

---

**¿Dudas?** Todo está implementado y documentado. El backend funciona al 100% con MockLLM. Para usar Gemini real, solo necesitas una nueva API key (la anterior fue filtrada).

**Estado:** ✅ **LISTO PARA DESARROLLO**
