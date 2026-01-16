/*
 * TumorGrowthModelTests.cs
 * Tests unitarios para TumorGrowthModel
 * 
 * Framework: NUnit 3.13
 * Valida: Ecuaciones Gompertz, progresión temporal, staging
 */

using NUnit.Framework;
using System;
using LungCancerVR.MathModel;

namespace LungCancerVR.Tests
{
    [TestFixture]
    public class TumorGrowthModelTests
    {
        private PatientProfile defaultPatient;
        
        [SetUp]
        public void Setup()
        {
            defaultPatient = new PatientProfile(
                age: 60,
                isSmoker: false,
                packYears: 0,
                diet: DietType.Normal
            );
        }
        
        [Test]
        public void TumorGrowthModel_Initialize_SetsDefaultValues()
        {
            var model = new TumorGrowthModel(defaultPatient);
            
            Assert.AreEqual(0.0f, model.SensitiveCells, 0.001f);
            Assert.AreEqual(0.0f, model.ResistantCells, 0.001f);
            Assert.AreEqual(0.0f, model.CurrentTime, 0.001f);
        }
        
        [Test]
        public void TumorGrowthModel_SetInitialConditions_UpdatesCells()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(100.0f, 10.0f);
            
            Assert.AreEqual(100.0f, model.SensitiveCells, 0.001f);
            Assert.AreEqual(10.0f, model.ResistantCells, 0.001f);
            Assert.AreEqual(110.0f, model.TotalCells, 0.001f);
        }
        
        [Test]
        public void TumorGrowthModel_Simulate_IncreasesTime()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(50.0f, 5.0f);
            
            model.Simulate(1.0f);
            
            Assert.AreEqual(1.0f, model.CurrentTime, 0.001f);
        }
        
        [Test]
        public void TumorGrowthModel_Simulate_GrowthWithoutTreatment()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(10.0f, 1.0f); // Pequeño tumor inicial
            
            float initialTotal = model.TotalCells;
            
            // Simular 10 días
            for (int i = 0; i < 10; i++)
            {
                model.Simulate(1.0f);
            }
            
            // El tumor debe crecer
            Assert.Greater(model.TotalCells, initialTotal);
        }
        
        [Test]
        public void TumorGrowthModel_Simulate_CarryingCapacityLimit()
        {
            var model = new TumorGrowthModel(defaultPatient);
            float K = model.K; // Capacidad de carga
            
            // Iniciar cerca de capacidad
            model.SetInitialConditions(K - 100.0f, 50.0f);
            
            // Simular mucho tiempo
            for (int i = 0; i < 100; i++)
            {
                model.Simulate(1.0f);
            }
            
            // No debe exceder K significativamente
            Assert.LessOrEqual(model.TotalCells, K * 1.01f); // 1% margen
        }
        
        [Test]
        public void TumorGrowthModel_ChemotherapyReducesSensitiveCells()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(100.0f, 10.0f);
            
            float initialSensitive = model.SensitiveCells;
            
            // Aplicar quimioterapia
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            // Simular 10 días
            for (int i = 0; i < 10; i++)
            {
                model.Simulate(1.0f);
            }
            
            // Células sensibles deben disminuir
            Assert.Less(model.SensitiveCells, initialSensitive);
        }
        
        [Test]
        public void TumorGrowthModel_ResistanceGrowthRate()
        {
            var model = new TumorGrowthModel(defaultPatient);
            
            // Verificar que rr < rs (resistentes crecen más lento)
            float rs = model.GetAdjustedRs();
            float rr = model.GetAdjustedRr();
            
            Assert.Less(rr, rs);
            Assert.AreEqual(rr, rs * 0.8f, 0.01f); // rr = 0.8 * rs
        }
        
        [Test]
        public void TumorGrowthModel_GetApproximateStage_EarlyStage()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(5.0f, 0.5f); // ~6 cm³ total
            
            string stage = model.GetApproximateStage();
            
            Assert.AreEqual("IA", stage);
        }
        
        [Test]
        public void TumorGrowthModel_GetApproximateStage_AdvancedStage()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(1000.0f, 200.0f); // Grande
            
            string stage = model.GetApproximateStage();
            
            Assert.IsTrue(stage == "IIIB" || stage == "IVA");
        }
        
        [Test]
        public void TumorGrowthModel_GetDoublingTime_RealisticValue()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(50.0f, 5.0f);
            
            float doublingTime = model.GetDoublingTime();
            
            // SCLC: 30-90 días típico
            Assert.Greater(doublingTime, 20.0f);
            Assert.Less(doublingTime, 200.0f);
        }
        
        [Test]
        public void TumorGrowthModel_GetResistanceFraction()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(90.0f, 10.0f); // 10% resistente
            
            float fraction = model.GetResistanceFraction();
            
            Assert.AreEqual(0.1f, fraction, 0.01f);
        }
        
        [Test]
        public void TumorGrowthModel_NegativeCellsProtection()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(1.0f, 0.1f); // Tumor muy pequeño
            
            // Quimio agresiva
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            // Simular hasta posible valor negativo
            for (int i = 0; i < 50; i++)
            {
                model.Simulate(1.0f);
            }
            
            // No debe haber valores negativos
            Assert.GreaterOrEqual(model.SensitiveCells, 0.0f);
            Assert.GreaterOrEqual(model.ResistantCells, 0.0f);
        }
        
        [Test]
        public void TumorGrowthModel_PatientFactorsAffectGrowth()
        {
            // Paciente joven sano
            var youngPatient = new PatientProfile(40, false, 0, DietType.Healthy);
            var youngModel = new TumorGrowthModel(youngPatient);
            youngModel.SetInitialConditions(10.0f, 1.0f);
            
            // Paciente mayor fumador
            var oldPatient = new PatientProfile(75, true, 40, DietType.Poor);
            var oldModel = new TumorGrowthModel(oldPatient);
            oldModel.SetInitialConditions(10.0f, 1.0f);
            
            // Simular 30 días
            for (int i = 0; i < 30; i++)
            {
                youngModel.Simulate(1.0f);
                oldModel.Simulate(1.0f);
            }
            
            // Paciente mayor debe tener tumor mayor
            Assert.Greater(oldModel.TotalCells, youngModel.TotalCells);
        }
        
        [Test]
        public void TumorGrowthModel_SimulateHistory_ReturnsTrajectory()
        {
            var model = new TumorGrowthModel(defaultPatient);
            model.SetInitialConditions(10.0f, 1.0f);
            
            var history = model.SimulateWithHistory(10.0f, 1.0f);
            
            Assert.IsNotNull(history);
            Assert.Greater(history.Length, 1); // Al menos 2 puntos
            
            // Primer punto es condición inicial
            Assert.AreEqual(10.0f, history[0][0], 0.1f);
            Assert.AreEqual(1.0f, history[0][1], 0.1f);
        }
    }
}
