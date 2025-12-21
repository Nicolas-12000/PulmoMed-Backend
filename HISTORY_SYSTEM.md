# Sistema de Historial Tipo Git para Simulaciones

## 📋 Resumen

Sistema de historial optimizado que permite **avanzar, retroceder y experimentar** en el modo libre sin guardar estado completo en cada paso. Funciona como Git: **snapshots completos + deltas incrementales**.

---

## 🎯 Problema Resuelto

### ❌ Problema: Historial tradicional
```python
# Guardar todo el estado cada paso
history = [
    {t: 0, Ns: 10, Nr: 1, ...},     # 100 bytes
    {t: 1, Ns: 10.5, Nr: 1.1, ...}, # 100 bytes
    {t: 2, Ns: 11, Nr: 1.2, ...},   # 100 bytes
    # ...
    {t: 730, Ns: 150, Nr: 50, ...}  # 100 bytes
]
# Simular 2 años = 730 pasos × 100 bytes = 73 KB por simulación
# 100 pacientes = 7.3 MB
```

### ✅ Solución: Snapshots + Deltas
```python
# Snapshot cada 100 días + deltas intermedios
history = {
    "snapshots": [
        {t: 0, Ns: 10, Nr: 1, ...},    # 100 bytes
        {t: 100, Ns: 50, Nr: 10, ...}, # 100 bytes
        {t: 200, Ns: 80, Nr: 20, ...}, # 100 bytes
        # ...
    ],
    "deltas": [
        {dt: 1, dNs: 0.5, dNr: 0.1},   # 25 bytes
        {dt: 1, dNs: 0.5, dNr: 0.1},   # 25 bytes
        # ...
    ]
}
# Simular 2 años = 7 snapshots × 100 + 723 deltas × 25 = 18.8 KB
# 100 pacientes = 1.88 MB
# AHORRO: 74% de memoria
```

---

## 🏗️ Arquitectura

### Componentes

```
SimulationHistory
├── HistoryNode (árbol)
│   ├── Snapshot (checkpoint completo)
│   ├── Deltas[] (cambios incrementales)
│   ├── Parent (nodo anterior)
│   └── Children[] (branches posibles)
│
├── Configuración
│   ├── snapshot_interval: int (cada N pasos crear snapshot)
│   └── max_deltas: int (máximo deltas entre snapshots)
│
└── Operaciones
    ├── save_state() - Guardar estado actual
    ├── rewind() - Retroceder en el tiempo
    ├── fast_forward() - Avanzar en el tiempo
    ├── create_branch() - Experimentar sin perder historial
    └── go_to_checkpoint() - Saltar a punto específico
```

### Flujo de Datos

```
┌─────────────┐
│   t = 0     │ → Snapshot #1 (estado completo)
└─────────────┘
      ↓ +1 día (delta)
┌─────────────┐
│   t = 1     │ → Delta (solo cambios)
└─────────────┘
      ↓ +1 día (delta)
┌─────────────┐
│   t = 2     │ → Delta
└─────────────┘
      ... (98 deltas más)
      ↓
┌─────────────┐
│   t = 100   │ → Snapshot #2 (nuevo checkpoint)
└─────────────┘
```

---

## 💻 Uso en Python (Backend)

### 1. Inicialización

```python
from app.services.simulation_history_service import SimulationHistory

# Crear historial (snapshot cada 30 días, máximo 50 deltas)
history = SimulationHistory(
    snapshot_interval=30,
    max_deltas=50
)

# Estado inicial del paciente
initial_state = {
    "volumen_tumor_sensible": 10.0,
    "volumen_tumor_resistente": 1.0,
    "tratamiento_activo": "ninguno",
    "dias_tratamiento": 0
}

# Inicializar historial
checkpoint_id = history.initialize(initial_state, "Tumor detectado")
```

### 2. Guardar Estados Durante Simulación

```python
# Simular 60 días sin tratamiento
for day in range(1, 61):
    # ... simular 1 día ...
    
    # Guardar estado cada 5 días
    if day % 5 == 0:
        state = {
            "volumen_tumor_sensible": model.sensitive_cells,
            "volumen_tumor_resistente": model.resistant_cells,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": day
        }
        
        # Automáticamente crea delta o snapshot según config
        tipo, id = history.save_state(state)
        print(f"Día {day}: Guardado como {tipo}")
```

### 3. Crear Checkpoint y Branch

```python
# Crear checkpoint importante (forzar snapshot)
state_before_treatment = {...}
history.save_state(state_before_treatment, force_snapshot=True)

# Crear branch para experimentar
checkpoint_id = history.create_branch("timeline-quimio")
print(f"Checkpoint creado: {checkpoint_id}")
```

### 4. Retroceder en el Tiempo

```python
# Probar quimioterapia
for day in range(1, 91):
    # ... simular con quimioterapia ...
    pass

volume_chemo = model.total_cells

# Retroceder al checkpoint
restored_state = history.rewind()

# Ahora probar inmunoterapia desde el mismo punto
for day in range(1, 91):
    # ... simular con inmunoterapia ...
    pass

volume_immuno = model.total_cells

# Comparar resultados
print(f"Quimio: {volume_chemo:.2f} cm³")
print(f"Inmuno: {volume_immuno:.2f} cm³")
```

### 5. Navegar por Checkpoints

```python
# Listar checkpoints disponibles
checkpoints = history.get_checkpoints()

for cp in checkpoints:
    print(f"[{cp['id'][:8]}] Día {cp['time']}: {cp['description']}")
    print(f"  Volumen: {cp['total_volume']:.2f} cm³")

# Saltar a checkpoint específico
history.go_to_checkpoint(checkpoint_id)
```

### 6. Estadísticas de Memoria

```python
stats = history.get_statistics()

print(f"Snapshots: {stats['total_snapshots']}")
print(f"Deltas: {stats['total_deltas']}")
print(f"Memoria: {stats['memory_usage']['total_kb']:.2f} KB")
print(f"Branch actual: {stats['current_branch']}")
```

---

## 🎮 Uso en Unity (C#)

### 1. Inicialización

```csharp
using LungCancerVR.MathModel;

// Crear historial
var history = new SimulationHistory(
    snapshotInterval: 30,  // Snapshot cada 30 días
    maxDeltas: 50           // Máximo 50 deltas
);

// Inicializar con modelo actual
history.Initialize(tumorModel, "none", "Tumor detectado");
```

### 2. Guardar en Update Loop

```csharp
public class SimulationManager : MonoBehaviour
{
    private TumorGrowthModel model;
    private SimulationHistory history;
    private string currentTreatment = "none";
    
    void Update()
    {
        float deltaTime = Time.deltaTime * daysPerSecond;
        model.Simulate(deltaTime);
        
        // Guardar estado cada segundo real
        if (Time.frameCount % 60 == 0)
        {
            history.SaveState(model, currentTreatment);
        }
    }
}
```

### 3. UI de Control Temporal

```csharp
public void OnRewindButtonClicked()
{
    bool success = history.Rewind(model, steps: 1);
    
    if (success)
    {
        Debug.Log($"Retrocedido a día {model.CurrentTime}");
        UpdateVisualization();
    }
}

public void OnFastForwardButtonClicked()
{
    bool success = history.FastForward(model, steps: 1);
    
    if (success)
    {
        Debug.Log($"Avanzado a día {model.CurrentTime}");
        UpdateVisualization();
    }
}

public void OnCreateCheckpointClicked()
{
    string checkpointId = history.CreateBranch("experimental");
    history.SaveState(model, currentTreatment, forceSnapshot: true);
    
    Debug.Log($"Checkpoint creado: {checkpointId}");
}
```

### 4. Menú de Checkpoints

```csharp
public void ShowCheckpointsMenu()
{
    var checkpoints = history.GetCheckpoints();
    
    foreach (var (id, time, description) in checkpoints)
    {
        // Crear botón en UI
        CreateCheckpointButton(id, $"Día {time:F0}: {description}", () =>
        {
            history.GoToCheckpoint(model, id);
            UpdateVisualization();
        });
    }
}
```

---

## 📊 Ejemplo de Ahorro de Memoria

### Escenario: Simular 2 años (730 días)

| Método | Snapshots | Deltas | Memoria Total | Ahorro |
|--------|-----------|--------|---------------|--------|
| **Tradicional** (todo) | 730 | 0 | 73 KB | 0% |
| **Git** (interval=30) | 24 | 706 | 19.7 KB | **73%** |
| **Git** (interval=50) | 15 | 715 | 19.4 KB | **74%** |
| **Git** (interval=100) | 8 | 722 | 18.9 KB | **74%** |

### Memoria por Usuario

| Usuarios | Tradicional | Git System | Ahorro Total |
|----------|-------------|------------|--------------|
| 1 | 73 KB | 19 KB | 54 KB |
| 10 | 730 KB | 190 KB | 540 KB |
| 100 | 7.3 MB | 1.9 MB | **5.4 MB** |
| 1000 | 73 MB | 19 MB | **54 MB** |

---

## ⚙️ Configuración Recomendada

### Por Tipo de Simulación

**Modo Exploración Rápida:**
```python
history = SimulationHistory(
    snapshot_interval=10,   # Snapshot cada 10 días
    max_deltas=20           # Pocos deltas = más snapshots
)
# Prioriza velocidad de navegación sobre memoria
```

**Modo Simulación Larga (años):**
```python
history = SimulationHistory(
    snapshot_interval=100,  # Snapshot cada 100 días
    max_deltas=100          # Muchos deltas = menos snapshots
)
# Prioriza ahorro de memoria sobre velocidad
```

**Modo Producción (balance):**
```python
history = SimulationHistory(
    snapshot_interval=30,   # Snapshot cada mes
    max_deltas=50           # Balance memoria/velocidad
)
# Balance óptimo entre memoria y performance
```

---

## 🧪 Tests

### Python

```bash
# Ejecutar tests del sistema de historial
pytest tests/unit/test_simulation_history.py -v

# Resultados: 17/17 tests pasados ✅
# - Snapshots
# - Deltas
# - Rewind/Fast-forward
# - Branching
# - Memoria
```

### Validación Matemática

```bash
# Validar lógica matemática del modelo C#
pytest tests/test_csharp_math_validation.py -v

# Resultados: 21/21 tests pasados ✅
```

---

## 🎯 Casos de Uso

### 1. Experimentar Tratamientos

```python
# Punto de decisión: día 60
checkpoint = history.create_branch("decision-point")

# Timeline A: Quimio
apply_chemotherapy()
simulate(90)
result_chemo = get_outcome()

# Volver al punto de decisión
history.go_to_checkpoint(checkpoint)

# Timeline B: Inmuno
apply_immunotherapy()
simulate(90)
result_immuno = get_outcome()

# Comparar y elegir mejor opción
best_treatment = choose_best(result_chemo, result_immuno)
```

### 2. Educación Médica

```python
# Estudiante explora diferentes escenarios
history.initialize(patient_case)

# Estudiante prueba tratamiento incorrecto
apply_treatment_A()
# ... tumor progresa ...

# Profesor: "Retrocede y prueba otra cosa"
history.rewind()

# Estudiante intenta tratamiento correcto
apply_treatment_B()
# ... tumor responde bien ...
```

### 3. Simulación Acelerada

```python
# Usuario quiere "avanzar 2 años"
for year in range(2):
    for day in range(365):
        model.simulate(1.0)
        
        # Solo guardar cada 10 días
        if day % 10 == 0:
            history.save_state(state)

# Memoria usada: ~7 KB en lugar de 73 KB
```

---

## 🚀 Próximas Mejoras

1. **Compresión de deltas**: Comprimir deltas antiguos con zlib
2. **Persistencia**: Guardar historial en SQLite/MongoDB
3. **Merge de branches**: Combinar múltiples timelines
4. **Auto-cleanup**: Eliminar checkpoints antiguos automáticamente
5. **Diff visual**: Mostrar diferencias entre checkpoints en UI

---

## 📝 Resumen

**Sistema de Historial Tipo Git:**
- ✅ **Ahorra 74% de memoria** vs historial tradicional
- ✅ **Permite retroceder/avanzar** en el tiempo
- ✅ **Branching** para experimentar sin perder datos
- ✅ **17 tests unitarios** validados
- ✅ **Compatible** Python (backend) y C# (Unity)
- ✅ **Optimizado** para simulaciones de años

**Implementación completa en:**
- Python: `app/services/simulation_history_service.py`
- C#: `CSharp_MathModel/Core/SimulationHistory.cs`
- Tests: `tests/unit/test_simulation_history.py`
- Ejemplo: `CSharp_MathModel/Examples/HistoryExample.cs`
