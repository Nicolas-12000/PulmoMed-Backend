/*
 * IntegrationTests.cs
 * Tests de integración end-to-end
 * 
 * Valida: Flujos completos, interacción entre componentes, escenarios realistas
 */

using NUnit.Framework;
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using LungCancerVR.MathModel;

namespace LungCancerVR.Tests
{
    [TestFixture]
    public class IntegrationTests
    {
        [Test]
        public void Integration_CompletePatientJourney_StageProgression()
        {
            // Simular journey completo de paciente desde detección hasta tratamiento
            
            // 1. Paciente detectado en estadio temprano
            var patient = new PatientProfile(
                age: 62,
                isSmoker: true,
                packYears: 35,
                diet: DietType.Poor
            );
            
            Assert.IsTrue(patient.Validate(), "Perfil de paciente debe ser válido");
            
            // 2. Tumor pequeño detectado (Estadio IA)
            var model = new TumorGrowthModel(patient);
            model.SetInitialConditions(5.0f, 0.5f); // 5.5 cm³ total
            
            Assert.AreEqual("IA", model.GetApproximateStage());
            
            // 3. Observar sin tratamiento por 60 días (decisión clínica)
            for (int i = 0; i < 60; i++)
            {
                model.Simulate(1.0f);
            }
            
            float volumeBeforeTreatment = model.TotalCells;
            string stageBeforeTreatment = model.GetApproximateStage();
            
            Assert.Greater(volumeBeforeTreatment, 5.5f, "Tumor debe haber crecido");
            
            // 4. Iniciar quimioterapia
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            // 5. Tratamiento por 90 días
            for (int i = 0; i < 90; i++)
            {
                model.Simulate(1.0f);
            }
            
            float volumeAfterTreatment = model.TotalCells;
            
            // 6. Verificar respuesta al tratamiento
            Assert.Less(volumeAfterTreatment, volumeBeforeTreatment, 
                "Volumen debe reducirse con quimioterapia");
            
            // 7. Verificar desarrollo de resistencia
            float resistanceFraction = model.GetResistanceFraction();
            Assert.Greater(resistanceFraction, 0.15f, 
                "Debe desarrollarse resistencia con tratamiento prolongado");
        }
        
        [Test]
        public void Integration_TreatmentSwitch_ResistanceDevelopment()
        {
            // Simular cambio de tratamiento debido a resistencia
            
            var patient = new PatientProfile(58, true, 30, DietType.Normal);
            var model = new TumorGrowthModel(patient);
            model.SetInitialConditions(20.0f, 5.0f); // Estadio IB
            
            // Fase 1: Quimioterapia inicial
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            for (int i = 0; i < 60; i++)
            {
                model.Simulate(1.0f);
            }
            
            float volumeAfterChemo = model.TotalCells;
            float resistanceAfterChemo = model.GetResistanceFraction();
            
            // Fase 2: Cambiar a inmunoterapia por resistencia
            model.SetTreatment(TreatmentType.Immunotherapy);
            
            for (int i = 0; i < 60; i++)
            {
                model.Simulate(1.0f);
            }
            
            float volumeAfterImmuno = model.TotalCells;
            float resistanceAfterImmuno = model.GetResistanceFraction();
            
            // Inmunoterapia debe mantener control o mejorar
            Assert.LessOrEqual(volumeAfterImmuno, volumeAfterChemo * 1.5f,
                "Inmunoterapia debe controlar el tumor");
        }
        
        [Test]
        public void Integration_SimulationState_Serialization()
        {
            // Verificar serialización completa para backend
            
            var patient = new PatientProfile(65, true, 40, DietType.Healthy);
            var model = new TumorGrowthModel(patient);
            model.SetInitialConditions(15.0f, 3.0f);
            model.SetTreatment(TreatmentType.Radiotherapy);
            
            // Simular 30 días
            for (int i = 0; i < 30; i++)
            {
                model.Simulate(1.0f);
            }
            
            // Crear SimulationState
            var state = SimulationState.FromModel(model, patient);
            state.ActiveTreatment = "radio";
            state.Mode = "libre";
            
            // Serializar a JSON
            var json = JsonSerializer.Serialize(state, new JsonSerializerOptions
            {
                WriteIndented = true
            });
            
            Assert.IsNotEmpty(json);
            Assert.IsTrue(json.Contains("edad"));
            Assert.IsTrue(json.Contains("volumen_tumor_sensible"));
            
            // Deserializar
            var deserialized = JsonSerializer.Deserialize<SimulationState>(json);
            
            Assert.IsNotNull(deserialized);
            Assert.AreEqual(state.Age, deserialized.Age);
            Assert.AreEqual(state.SensitiveTumorVolume, deserialized.SensitiveTumorVolume, 0.01f);
            Assert.AreEqual(state.ResistantTumorVolume, deserialized.ResistantTumorVolume, 0.01f);
        }
        
        [Test]
        public void Integration_MultiplePatients_ComparativeOutcomes()
        {
            // Comparar evolución de 3 perfiles diferentes
            
            // Paciente 1: Joven, no fumador, sano
            var patient1 = new PatientProfile(45, false, 0, DietType.Healthy);
            var model1 = new TumorGrowthModel(patient1);
            model1.SetInitialConditions(10.0f, 1.0f);
            
            // Paciente 2: Mayor, fumador leve
            var patient2 = new PatientProfile(70, true, 20, DietType.Normal);
            var model2 = new TumorGrowthModel(patient2);
            model2.SetInitialConditions(10.0f, 1.0f);
            
            // Paciente 3: Mayor, fumador pesado, mala dieta
            var patient3 = new PatientProfile(75, true, 50, DietType.Poor);
            var model3 = new TumorGrowthModel(patient3);
            model3.SetInitialConditions(10.0f, 1.0f);
            
            // Simular 90 días sin tratamiento
            for (int i = 0; i < 90; i++)
            {
                model1.Simulate(1.0f);
                model2.Simulate(1.0f);
                model3.Simulate(1.0f);
            }
            
            // Verificar gradiente de progresión
            Assert.Less(model1.TotalCells, model2.TotalCells,
                "Paciente joven debe progresar más lento que mayor");
            
            Assert.Less(model2.TotalCells, model3.TotalCells,
                "Paciente con factores moderados debe progresar más lento que alto riesgo");
            
            // Verificar tiempos de duplicación
            float dt1 = model1.GetDoublingTime();
            float dt2 = model2.GetDoublingTime();
            float dt3 = model3.GetDoublingTime();
            
            Assert.Greater(dt1, dt2, "Paciente joven debe tener mayor tiempo de duplicación");
            Assert.Greater(dt2, dt3, "Gradiente de tiempos debe ser consistente");
        }
        
        [Test]
        public void Integration_SimulateWithHistory_DataValidation()
        {
            // Verificar trayectoria completa de simulación
            
            var patient = new PatientProfile(60, false, 0, DietType.Normal);
            var model = new TumorGrowthModel(patient);
            model.SetInitialConditions(8.0f, 1.0f);
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            // Obtener historia completa
            var history = model.SimulateWithHistory(30.0f, 1.0f);
            
            Assert.IsNotNull(history);
            Assert.GreaterOrEqual(history.Length, 2);
            
            // Verificar que primer punto es condición inicial
            Assert.AreEqual(8.0f, history[0][0], 0.5f);
            Assert.AreEqual(1.0f, history[0][1], 0.2f);
            
            // Verificar tendencias
            bool hasSensitiveDecrease = false;
            for (int i = 1; i < history.Length; i++)
            {
                float prevSensitive = history[i - 1][0];
                float currSensitive = history[i][0];
                
                if (currSensitive < prevSensitive)
                {
                    hasSensitiveDecrease = true;
                    break;
                }
            }
            
            Assert.IsTrue(hasSensitiveDecrease, 
                "Células sensibles deben disminuir con quimioterapia en algún punto");
        }
        
        [Test]
        public void Integration_ExtremeCases_Stability()
        {
            // Verificar estabilidad en casos extremos
            
            var patient = new PatientProfile(60, false, 0, DietType.Normal);
            var model = new TumorGrowthModel(patient);
            
            // Caso 1: Tumor microscópico
            model.SetInitialConditions(0.1f, 0.01f);
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            for (int i = 0; i < 30; i++)
            {
                model.Simulate(1.0f);
            }
            
            Assert.GreaterOrEqual(model.SensitiveCells, 0.0f, "No debe haber valores negativos");
            Assert.GreaterOrEqual(model.ResistantCells, 0.0f, "No debe haber valores negativos");
            
            // Caso 2: Tumor muy grande (cerca de K)
            model = new TumorGrowthModel(patient);
            model.SetInitialConditions(200.0f, 40.0f); // Cerca de K=250
            
            for (int i = 0; i < 60; i++)
            {
                model.Simulate(1.0f);
            }
            
            Assert.LessOrEqual(model.TotalCells, model.K * 1.05f,
                "No debe exceder significativamente la capacidad de carga");
        }
        
        [Test]
        public void Integration_SEERCase_RealisticScenario()
        {
            // Simular caso basado en estadísticas SEER
            // Caso: Estadio IIIA, fumador activo, 60 años
            
            var patient = new PatientProfile(
                age: 60,
                isSmoker: true,
                packYears: 45,
                diet: DietType.Poor
            );
            
            var model = new TumorGrowthModel(patient);
            
            // Estadio IIIA: ~114-180 cm³
            model.SetInitialConditions(120.0f, 30.0f); // 150 cm³ total, 20% resistente
            
            Assert.AreEqual("IIIA", model.GetApproximateStage());
            
            // Protocolo: Quimio + Radio combinado (simplificado como quimio)
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            // Simular 6 meses de tratamiento (180 días)
            for (int i = 0; i < 180; i++)
            {
                model.Simulate(1.0f);
            }
            
            float finalVolume = model.TotalCells;
            string finalStage = model.GetApproximateStage();
            float finalResistance = model.GetResistanceFraction();
            
            // Según SEER, esperamos respuesta parcial o progresión limitada
            Assert.Less(finalVolume, 300.0f, 
                "Con tratamiento, no debe progresar masivamente");
            
            Assert.Greater(finalResistance, 0.3f,
                "Resistencia debe aumentar significativamente en IIIA tratado");
            
            // Logging para análisis
            Console.WriteLine($"SEER Case Results:");
            Console.WriteLine($"  Initial: 150 cm³, Stage IIIA");
            Console.WriteLine($"  Final: {finalVolume:F1} cm³, Stage {finalStage}");
            Console.WriteLine($"  Resistance: {finalResistance * 100:F1}%");
            Console.WriteLine($"  Doubling time: {model.GetDoublingTime():F1} days");
        }
    }
}
