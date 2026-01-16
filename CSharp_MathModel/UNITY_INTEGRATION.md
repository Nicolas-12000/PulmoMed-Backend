# Integración del Modelo Matemático con Unity

Este documento explica cómo importar y usar la librería `CSharp_MathModel` en un proyecto de Unity.

---

## 1. Importación de Archivos

### Estructura recomendada en Unity:
```
Assets/
├── Scripts/
│   └── MathModel/
│       ├── Core/
│       │   └── TumorGrowthModel.cs
│       ├── Treatments/
│       │   └── ITreatmentStrategy.cs
│       ├── Solvers/
│       │   └── RK4Solver.cs
│       └── Models/
│           ├── PatientProfile.cs
│           └── SimulationState.cs
```

### Pasos:
1. **Copiar archivos** desde `CSharp_MathModel/` a `Assets/Scripts/MathModel/`
2. **Excluir carpetas** de Tests y Examples (no son necesarias en Unity)
3. **Importar solo**:
   - `Core/TumorGrowthModel.cs`
   - `Treatments/ITreatmentStrategy.cs`
   - `Solvers/RK4Solver.cs`
   - `Models/PatientProfile.cs`
   - `Models/SimulationState.cs`

---

## 2. Namespace y Referencias

### Namespace del modelo:
```csharp
namespace LungCancerVR.MathModel
```

### Usar en scripts de Unity:
```csharp
using UnityEngine;
using LungCancerVR.MathModel;

public class TumorSimulationManager : MonoBehaviour
{
    private TumorGrowthModel tumorModel;
    private PatientProfile currentPatient;
    
    void Start()
    {
        // Crear paciente
        currentPatient = new PatientProfile(65, true, 30, DietType.Normal);
        
        // Crear modelo
        tumorModel = new TumorGrowthModel(currentPatient);
        tumorModel.SetInitialConditions(10.0f, 2.0f);
    }
}
```

---

## 3. Simulación en Update Loop

### Opción A: Tiempo real acelerado (recomendado)
```csharp
public class TumorSimulationManager : MonoBehaviour
{
    private TumorGrowthModel tumorModel;
    
    [Header("Simulation Settings")]
    [Tooltip("Velocidad de simulación (días por segundo)")]
    public float daysPerSecond = 5.0f; // 5 días simulados por segundo real
    
    void Update()
    {
        float deltaTime = Time.deltaTime * daysPerSecond;
        tumorModel.Simulate(deltaTime);
        
        // Actualizar UI
        UpdateVisualization();
    }
    
    void UpdateVisualization()
    {
        float totalCells = tumorModel.TotalCells;
        string stage = tumorModel.GetApproximateStage();
        
        Debug.Log($"Tumor: {totalCells:F2} cm³ - Estadio: {stage}");
    }
}
```

### Opción B: Simulación por pasos discretos
```csharp
public void SimulateDays(int days)
{
    for (int i = 0; i < days; i++)
    {
        tumorModel.Simulate(1.0f); // 1 día
    }
}

public void SimulateWeek()
{
    SimulateDays(7);
}
```

---

## 4. Cambio de Tratamientos en Runtime

### Script de control de tratamientos:
```csharp
public class TreatmentController : MonoBehaviour
{
    private TumorGrowthModel tumorModel;
    
    [Header("UI References")]
    public Button btnQuimio;
    public Button btnRadio;
    public Button btnImmuno;
    public Button btnStop;
    
    void Start()
    {
        btnQuimio.onClick.AddListener(() => ApplyTreatment(TreatmentType.Chemotherapy));
        btnRadio.onClick.AddListener(() => ApplyTreatment(TreatmentType.Radiotherapy));
        btnImmuno.onClick.AddListener(() => ApplyTreatment(TreatmentType.Immunotherapy));
        btnStop.onClick.AddListener(() => ApplyTreatment(TreatmentType.None));
    }
    
    void ApplyTreatment(TreatmentType treatment)
    {
        tumorModel.SetTreatment(treatment);
        Debug.Log($"Tratamiento aplicado: {treatment}");
    }
}
```

---

## 5. Visualización 3D del Tumor

### Script para escalar objeto 3D según volumen:
```csharp
public class TumorVisualizer : MonoBehaviour
{
    private TumorGrowthModel tumorModel;
    
    [Header("Visualization")]
    public GameObject tumorMesh;
    public Material sensitiveMaterial;
    public Material resistantMaterial;
    
    [Header("Scaling")]
    public float scaleFactor = 0.1f; // 1 cm³ = 0.1 unidades Unity
    
    void Update()
    {
        // Volumen total en cm³
        float totalVolume = tumorModel.TotalCells;
        
        // Radio esférico (V = 4/3 * π * r³)
        float radius = Mathf.Pow((3 * totalVolume) / (4 * Mathf.PI), 1.0f / 3.0f);
        
        // Escalar objeto
        float scale = radius * scaleFactor;
        tumorMesh.transform.localScale = new Vector3(scale, scale, scale);
        
        // Color según resistencia
        float resistanceFraction = tumorModel.GetResistanceFraction();
        tumorMesh.GetComponent<Renderer>().material.color = 
            Color.Lerp(sensitiveMaterial.color, resistantMaterial.color, resistanceFraction);
    }
}
```

---

## 6. Integración con Backend Python

### Script de comunicación HTTP:
```csharp
using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using LungCancerVR.MathModel;

public class BackendConnector : MonoBehaviour
{
    private const string BACKEND_URL = "http://localhost:8000";
    
    public IEnumerator ConsultarProfesorIA(SimulationState state, Action<TeacherResponse> callback)
    {
        string json = JsonUtility.ToJson(state);
        
        using (UnityWebRequest request = UnityWebRequest.Post(
            $"{BACKEND_URL}/api/profesor/consultar", 
            json, 
            "application/json"))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                string responseJson = request.downloadHandler.text;
                TeacherResponse response = JsonUtility.FromJson<TeacherResponse>(responseJson);
                callback?.Invoke(response);
            }
            else
            {
                Debug.LogError($"Error: {request.error}");
            }
        }
    }
}
```

### Uso en MonoBehaviour:
```csharp
public class AITeacherUI : MonoBehaviour
{
    private BackendConnector backend;
    
    void Start()
    {
        backend = GetComponent<BackendConnector>();
    }
    
    public void AskTeacher()
    {
        SimulationState state = CreateCurrentState();
        
        StartCoroutine(backend.ConsultarProfesorIA(state, OnResponseReceived));
    }
    
    void OnResponseReceived(TeacherResponse response)
    {
        Debug.Log($"Explicación: {response.Explicacion}");
        Debug.Log($"Recomendación: {response.Recomendacion}");
        
        // Actualizar UI con respuesta
        ShowResponse(response);
    }
}
```

---

## 7. Casos Predefinidos (Biblioteca SEER)

### Cargar caso desde backend:
```csharp
public IEnumerator CargarCaso(string casoId, Action<SimulationState> callback)
{
    using (UnityWebRequest request = UnityWebRequest.Get(
        $"{BACKEND_URL}/api/profesor/casos/{casoId}"))
    {
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            string json = request.downloadHandler.text;
            SimulationState caso = JsonUtility.FromJson<SimulationState>(json);
            callback?.Invoke(caso);
        }
    }
}

// Uso:
StartCoroutine(CargarCaso("estadio_ia_temprano", casoState => {
    // Aplicar caso al modelo
    var patient = new PatientProfile(
        casoState.Age,
        casoState.IsSmoker,
        casoState.PackYears,
        SimulationState.StringToDietType(casoState.Diet)
    );
    
    tumorModel = new TumorGrowthModel(patient);
    tumorModel.SetInitialConditions(
        casoState.SensitiveTumorVolume,
        casoState.ResistantTumorVolume
    );
}));
```

---

## 8. Performance en Unity

### Recomendaciones:
1. **No simular en Update()** si no es necesario - usar coroutines
2. **Cachear resultados** de `GetApproximateStage()` si se llama frecuentemente
3. **Usar Time.fixedDeltaTime** para física determinística
4. **Pool de objetos** para partículas de células

### Simulación optimizada:
```csharp
public class OptimizedSimulation : MonoBehaviour
{
    private TumorGrowthModel tumorModel;
    private float accumulatedTime = 0.0f;
    
    [Header("Performance")]
    public float updateInterval = 0.1f; // Actualizar cada 0.1 segundos
    
    void Update()
    {
        accumulatedTime += Time.deltaTime * daysPerSecond;
        
        if (accumulatedTime >= updateInterval)
        {
            tumorModel.Simulate(accumulatedTime);
            accumulatedTime = 0.0f;
            
            UpdateVisualization();
        }
    }
}
```

---

## 9. Debugging y Logs

### Logs útiles en Unity Console:
```csharp
void LogTumorState()
{
    Debug.Log($"[Tumor] Tiempo: {tumorModel.CurrentTime:F1} días");
    Debug.Log($"[Tumor] Volumen total: {tumorModel.TotalCells:F2} cm³");
    Debug.Log($"[Tumor] Sensibles: {tumorModel.SensitiveCells:F2} cm³");
    Debug.Log($"[Tumor] Resistentes: {tumorModel.ResistantCells:F2} cm³");
    Debug.Log($"[Tumor] Estadio: {tumorModel.GetApproximateStage()}");
    Debug.Log($"[Tumor] Tiempo duplicación: {tumorModel.GetDoublingTime():F1} días");
    Debug.Log($"[Tumor] Fracción resistente: {tumorModel.GetResistanceFraction() * 100:F1}%");
}
```

---

## 10. Compatibilidad

### Versiones probadas:
- ✅ Unity 2021.3 LTS (recomendado)
- ✅ Unity 2022.3 LTS
- ✅ Unity 2023.2

### Requisitos:
- C# 9.0 o superior
- Scripting Runtime: .NET Standard 2.1
- API Compatibility Level: .NET Standard 2.1

### Configuración en Unity:
```
Edit → Project Settings → Player → Other Settings:
- Scripting Runtime Version: .NET Standard 2.1
- API Compatibility Level: .NET Standard 2.1
- C# Compiler: Roslyn (default)
```

---

## 11. Troubleshooting

### Error: "Namespace no encontrado"
**Solución**: Verifica que los archivos estén en `Assets/Scripts/` y que Unity haya recompilado.

### Error: "System.Text.Json no encontrado"
**Solución**: Usa `JsonUtility` de Unity en lugar de `System.Text.Json`:
```csharp
// En lugar de:
JsonSerializer.Serialize(state)

// Usar:
JsonUtility.ToJson(state)
```

### Simulación muy lenta
**Solución**: Reduce `daysPerSecond` o aumenta `updateInterval`.

### Backend no responde
**Solución**: Verifica que el backend Python esté corriendo con `uvicorn main:app --reload`.

---

## Contacto

Para dudas sobre la integración, contactar al equipo de backend Python.
