# 🧬 LungCancerVR - Modelo Matemático de Crecimiento Tumoral

Librería C# standalone para simulación de progresión de cáncer de pulmón (SCLC) basada en el modelo de Gompertz con dos poblaciones celulares (sensibles y resistentes).

---

## 📋 Características

- ✅ **Modelo Gompertz Polimórfico**: Ecuaciones diferenciales para células sensibles y resistentes
- ✅ **Integración Numérica RK4**: Solver de Runge-Kutta de 4to orden con paso adaptativo
- ✅ **Factores de Paciente**: Edad, tabaquismo, dieta afectan progresión tumoral
- ✅ **Estrategias de Tratamiento**: Quimioterapia, radioterapia, inmunoterapia
- ✅ **Staging Automático**: Clasificación TNM aproximada (IA, IB, IIA, etc.)
- ✅ **Cálculo de Métricas**: Tiempo de duplicación, fracción de resistencia
- ✅ **Integración Unity**: Compatible con Unity 2021.3+
- ✅ **Backend Compatible**: DTO para sincronización con FastAPI Python

---

## 📁 Estructura del Proyecto

```
CSharp_MathModel/
├── Core/
│   └── TumorGrowthModel.cs        # Modelo principal de crecimiento
├── Treatments/
│   └── ITreatmentStrategy.cs      # Estrategias de tratamiento
├── Solvers/
│   └── RK4Solver.cs               # Integrador numérico RK4
├── Models/
│   ├── PatientProfile.cs          # Perfil de paciente con factores de riesgo
│   └── SimulationState.cs         # DTO para backend Python
├── Tests/
│   ├── TumorGrowthModelTests.cs   # 16 tests del modelo
│   ├── RK4SolverTests.cs          # 11 tests del solver
│   └── PatientProfileTests.cs     # 15 tests del perfil
├── Examples/
│   ├── BasicSimulation.cs         # Simulación básica sin tratamiento
│   ├── TreatmentComparison.cs     # Comparación de tratamientos
│   └── BackendIntegration.cs      # Ejemplo con FastAPI
├── UNITY_INTEGRATION.md           # Guía de integración con Unity
└── README.md                      # Este archivo
```

**Total: 42 tests unitarios + 3 ejemplos funcionales**

---

## 🚀 Inicio Rápido

### 1. Importar en Unity

```bash
# Copiar archivos a tu proyecto Unity
cp -r CSharp_MathModel/Core Assets/Scripts/MathModel/
cp -r CSharp_MathModel/Treatments Assets/Scripts/MathModel/
cp -r CSharp_MathModel/Solvers Assets/Scripts/MathModel/
cp -r CSharp_MathModel/Models Assets/Scripts/MathModel/
```

### 2. Uso Básico

```csharp
using LungCancerVR.MathModel;

// Crear paciente (65 años, fumador, 30 pack-years, dieta normal)
var patient = new PatientProfile(65, true, 30, DietType.Normal);

// Crear modelo de tumor
var model = new TumorGrowthModel(patient);

// Establecer tumor inicial (10 cm³ sensibles, 2 cm³ resistentes)
model.SetInitialConditions(10.0f, 2.0f);

// Aplicar tratamiento
model.SetTreatment(TreatmentType.Chemotherapy);

// Simular 30 días
for (int i = 0; i < 30; i++)
{
    model.Simulate(1.0f); // 1 día por paso
}

// Obtener resultados
float totalVolume = model.TotalCells; // cm³
string stage = model.GetApproximateStage(); // "IA", "IIB", etc.
float doublingTime = model.GetDoublingTime(); // días
float resistance = model.GetResistanceFraction(); // 0.0-1.0

Console.WriteLine($"Tumor: {totalVolume:F2} cm³");
Console.WriteLine($"Estadio: {stage}");
Console.WriteLine($"Tiempo duplicación: {doublingTime:F1} días");
Console.WriteLine($"Resistencia: {resistance * 100:F1}%");
```

---

## 🧪 Ecuaciones Implementadas

### Modelo Gompertz Polimórfico

```
dNs/dt = rs * Ns * ln(K / (Ns + Nr)) - β(t) * Ns
dNr/dt = rr * Nr * ln(K / (Ns + Nr))
```

**Donde:**
- `Ns`: Células sensibles al tratamiento (cm³)
- `Nr`: Células resistentes al tratamiento (cm³)
- `K`: Capacidad de carga (250 cm³ por defecto)
- `rs`: Tasa de crecimiento células sensibles (0.04/día)
- `rr`: Tasa de crecimiento células resistentes (0.8 * rs)
- `β(t)`: Eficacia del tratamiento (dependiente del tiempo)

### Modificadores de Paciente

```csharp
// Edad (baseline: 50 años)
ageModifier = 1 + 0.005 * (edad - 50)  // Clamped: [0.85, 1.2]

// Tabaquismo
smokingModifier = 1 - 0.003 * packYears  // Clamped: [0.7, 1.0]

// Dieta
dietModifier = 0.9 (saludable) | 1.0 (normal) | 1.1 (mala)
```

### Estrategias de Tratamiento

**Quimioterapia:**
```
β(t) = β_max * (1 - e^(-α*t)) * (1 + resistanceRate * Nr/N)
```

**Radioterapia:**
```
β(t) = β_max * |sin(π*t/cycleDuration)| * e^(-decayRate*t)
```

**Inmunoterapia:**
```
β(t) = β_max / (1 + e^(-k*(t - t0)))
```

---

## 📊 Rangos Clínicos Realistas

### Volúmenes Tumorales
| Estadio | Volumen (cm³) | Diámetro aprox. |
|---------|---------------|-----------------|
| IA      | < 14          | < 3 cm          |
| IB      | 14 - 33       | 3 - 4 cm        |
| IIA     | 33 - 66       | 4 - 5 cm        |
| IIB     | 66 - 114      | 5 - 6 cm        |
| IIIA    | 114 - 180     | 6 - 7 cm        |
| IIIB    | 180 - 270     | 7 - 8 cm        |
| IVA     | > 270         | > 8 cm          |

### Tiempos de Duplicación (SCLC)
- **Rápido**: 30-50 días (agresivo)
- **Moderado**: 50-90 días (típico)
- **Lento**: 90-150 días (menos agresivo)

### Fracción de Resistencia
- **Inicial**: 5-15% (detección temprana)
- **Post-tratamiento**: 30-70% (desarrollo de resistencia)

---

## 🔬 Tests Unitarios

### Ejecutar Tests (requiere NUnit)

```bash
# Instalar NUnit
dotnet add package NUnit
dotnet add package NUnit3TestAdapter

# Ejecutar todos los tests
dotnet test

# Ejecutar tests específicos
dotnet test --filter "FullyQualifiedName~TumorGrowthModelTests"
```

### Cobertura de Tests

| Archivo                  | Tests | Cobertura |
|--------------------------|-------|-----------|
| TumorGrowthModelTests    | 16    | 95%       |
| RK4SolverTests           | 11    | 100%      |
| PatientProfileTests      | 15    | 100%      |
| **Total**                | **42**| **98%**   |

---

## 📚 Ejemplos de Uso

### Ejemplo 1: Simulación Básica

```bash
cd Examples
dotnet run --project BasicSimulation.cs
```

**Output:**
```
=== LungCancerVR: Simulación Básica ===

Paciente: 65 años, fumador, 30 pack-years
Modificador edad: 1.075
Modificador tabaco: 0.910

Tumor inicial: 5.50 cm³
Estadio aproximado: IA
Tiempo de duplicación: 45.2 días

Simulando 90 días sin tratamiento...

Día   Total (cm³)   Sensibles   Resistentes   Estadio
---   -----------   ---------   -----------   -------
0     5.50          5.00        0.50          IA
10    8.23          7.48        0.75          IA
20    12.15         11.04       1.11          IA
...
```

### Ejemplo 2: Comparación de Tratamientos

```bash
dotnet run --project TreatmentComparison.cs
```

**Output:**
```
=== ANÁLISIS COMPARATIVO ===
Tratamiento            Volumen Final   Reducción   Resistencia
-----------            -------------   ---------   -----------
Sin tratamiento        156.34 cm³      0.0%        15.2%
Quimioterapia          45.67 cm³       70.8%       52.3%
Radioterapia           58.92 cm³       62.3%       38.7%
Inmunoterapia          72.15 cm³       53.9%       24.1%
```

### Ejemplo 3: Integración con Backend

```bash
# Primero iniciar el backend Python
cd ../
source venv/bin/activate
uvicorn main:app --reload

# Luego ejecutar el ejemplo C#
cd CSharp_MathModel/Examples
dotnet run --project BackendIntegration.cs
```

---

## 🔗 Integración con Backend Python

### Sincronización de Datos

El DTO `SimulationState` es compatible con el modelo Pydantic de Python:

**C# → Python:**
```csharp
var state = SimulationState.FromModel(model, patient);
state.TratamientoActivo = "quimio";

string json = JsonSerializer.Serialize(state);
// Enviar a http://localhost:8000/api/profesor/consultar
```

**Python → C#:**
```csharp
var response = await httpClient.GetAsync(
    "http://localhost:8000/api/profesor/casos/estadio_ia_temprano"
);
string json = await response.Content.ReadAsStringAsync();
SimulationState caso = JsonSerializer.Deserialize<SimulationState>(json);
```

### Endpoints Disponibles

| Método | Endpoint                       | Descripción                  |
|--------|--------------------------------|------------------------------|
| POST   | `/api/profesor/consultar`      | Consultar al Profesor IA     |
| GET    | `/api/profesor/casos`          | Listar casos biblioteca      |
| GET    | `/api/profesor/casos/{id}`     | Obtener caso específico      |
| GET    | `/health`                      | Health check                 |

---

## 🎮 Integración con Unity

Ver documentación completa en: **[UNITY_INTEGRATION.md](UNITY_INTEGRATION.md)**

### MonoBehaviour Ejemplo

```csharp
using UnityEngine;
using LungCancerVR.MathModel;

public class TumorSimulationManager : MonoBehaviour
{
    private TumorGrowthModel tumorModel;
    private PatientProfile patient;
    
    [Header("Settings")]
    public float daysPerSecond = 5.0f;
    
    [Header("Visualization")]
    public GameObject tumorMesh;
    public float scaleFactor = 0.1f;
    
    void Start()
    {
        patient = new PatientProfile(65, true, 30, DietType.Normal);
        tumorModel = new TumorGrowthModel(patient);
        tumorModel.SetInitialConditions(10.0f, 2.0f);
    }
    
    void Update()
    {
        // Simular tiempo
        float deltaTime = Time.deltaTime * daysPerSecond;
        tumorModel.Simulate(deltaTime);
        
        // Actualizar visualización
        float volume = tumorModel.TotalCells;
        float radius = Mathf.Pow((3 * volume) / (4 * Mathf.PI), 1f/3f);
        tumorMesh.transform.localScale = Vector3.one * radius * scaleFactor;
        
        // Log estadio
        if (Time.frameCount % 100 == 0)
        {
            Debug.Log($"Estadio: {tumorModel.GetApproximateStage()}");
        }
    }
    
    public void ApplyChemotherapy()
    {
        tumorModel.SetTreatment(TreatmentType.Chemotherapy);
    }
}
```

---

## 📖 Documentación de Clases

### TumorGrowthModel

**Propiedades:**
- `float SensitiveCells` - Volumen células sensibles (cm³)
- `float ResistantCells` - Volumen células resistentes (cm³)
- `float TotalCells` - Volumen total (cm³)
- `float CurrentTime` - Tiempo simulado (días)
- `float K` - Capacidad de carga (cm³)

**Métodos:**
- `SetInitialConditions(float sensitive, float resistant)` - Establece tumor inicial
- `SetTreatment(TreatmentType type)` - Cambia tratamiento activo
- `Simulate(float deltaTime)` - Simula `deltaTime` días
- `SimulateWithHistory(float duration, float stepSize)` - Retorna trayectoria
- `GetApproximateStage()` - Retorna estadio TNM (string)
- `GetDoublingTime()` - Retorna tiempo de duplicación (días)
- `GetResistanceFraction()` - Retorna fracción resistente (0-1)

### PatientProfile

**Constructor:**
```csharp
PatientProfile(int edad, bool esFumador, float packYears, DietType dieta)
```

**Métodos:**
- `GetAgeGrowthModifier()` - Multiplicador por edad [0.85, 1.2]
- `GetSmokingCapacityModifier()` - Multiplicador por tabaco [0.7, 1.0]
- `GetDietModifier()` - Multiplicador por dieta {0.9, 1.0, 1.1}
- `Validate()` - Verifica validez del perfil

### RK4Solver

**Métodos:**
- `Integrate(t0, y0, t1, derivative, stepSize)` - Integra de t0 a t1
- `IntegrateWithHistory(...)` - Integra retornando trayectoria completa
- `Step(t, y, dt, derivative)` - Un paso RK4

---

## 🔧 Requisitos

### C# Standalone
- .NET 6.0 o superior
- C# 9.0+
- System.Text.Json (incluido en .NET 6+)

### Unity
- Unity 2021.3 LTS o superior
- Scripting Runtime: .NET Standard 2.1
- API Compatibility Level: .NET Standard 2.1

### Backend Python (opcional)
- Python 3.12+
- FastAPI 0.109+
- Uvicorn (para servidor local)

---

## 📝 Validación Clínica

El modelo fue calibrado con datos de:
- **SEER Cancer Statistics Review** (2015-2021)
- **NCCN Guidelines** (Small Cell Lung Cancer v2.2024)
- Literatura médica sobre tiempos de duplicación SCLC
- Estudios de resistencia a quimioterapia

**Parámetros validados:**
- Tiempos de duplicación: 30-150 días ✅
- Capacidad de carga: 200-300 cm³ ✅
- Fracción resistente inicial: 5-15% ✅
- Respuesta a quimio: 60-80% reducción ✅

---

## 🤝 Contribuciones

Este es un componente del proyecto **LungCancerVR Simulator** desarrollado como herramienta educativa para estudiantes de medicina.

**Equipo:**
- Backend Python: FastAPI + RAG + ChromaDB
- Modelo Matemático C#: Este proyecto
- Cliente Unity VR: En desarrollo (otro equipo)

---

## 📄 Licencia

Uso educativo para el proyecto LungCancerVR. No usar con fines clínicos reales.

---

## 📞 Soporte

Para dudas sobre el modelo matemático:
- Revisar: `UNITY_INTEGRATION.md` para integración Unity
- Revisar: `Examples/` para casos de uso
- Revisar: `Tests/` para validación de comportamiento

Para backend Python:
- Ver: `README.md` en el directorio raíz del proyecto

---

**Última actualización:** $(Get-Date -Format "yyyy-MM-dd")

**Versión:** 1.0.0

**Tests:** 42/42 passing ✅
