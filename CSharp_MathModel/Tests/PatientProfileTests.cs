/*
 * PatientProfileTests.cs
 * Tests unitarios para PatientProfile
 * 
 * Valida: Modificadores, validación, edge cases
 */

using NUnit.Framework;
using System;
using LungCancerVR.MathModel;

namespace LungCancerVR.Tests
{
    [TestFixture]
    public class PatientProfileTests
    {
        [Test]
        public void PatientProfile_DefaultConstructor()
        {
            var patient = new PatientProfile(60, false, 0, DietType.Normal);
            
            Assert.AreEqual(60, patient.Edad);
            Assert.IsFalse(patient.EsFumador);
            Assert.AreEqual(0, patient.PackYears);
            Assert.AreEqual(DietType.Normal, patient.Dieta);
        }
        
        [Test]
        public void PatientProfile_GetAgeGrowthModifier_Younger()
        {
            var patient = new PatientProfile(40, false, 0, DietType.Normal);
            
            float modifier = patient.GetAgeGrowthModifier();
            
            // edad < 50 → modifier < 1.0
            Assert.Less(modifier, 1.0f);
            Assert.AreEqual(0.95f, modifier, 0.01f); // 1 + 0.005*(40-50) = 0.95
        }
        
        [Test]
        public void PatientProfile_GetAgeGrowthModifier_Baseline()
        {
            var patient = new PatientProfile(50, false, 0, DietType.Normal);
            
            float modifier = patient.GetAgeGrowthModifier();
            
            Assert.AreEqual(1.0f, modifier, 0.001f);
        }
        
        [Test]
        public void PatientProfile_GetAgeGrowthModifier_Older()
        {
            var patient = new PatientProfile(70, false, 0, DietType.Normal);
            
            float modifier = patient.GetAgeGrowthModifier();
            
            // edad > 50 → modifier > 1.0
            Assert.Greater(modifier, 1.0f);
            Assert.AreEqual(1.1f, modifier, 0.01f); // 1 + 0.005*(70-50) = 1.1
        }
        
        [Test]
        public void PatientProfile_GetAgeGrowthModifier_ClampedMin()
        {
            var patient = new PatientProfile(20, false, 0, DietType.Normal);
            
            float modifier = patient.GetAgeGrowthModifier();
            
            Assert.GreaterOrEqual(modifier, 0.85f); // Clamped
        }
        
        [Test]
        public void PatientProfile_GetAgeGrowthModifier_ClampedMax()
        {
            var patient = new PatientProfile(90, false, 0, DietType.Normal);
            
            float modifier = patient.GetAgeGrowthModifier();
            
            Assert.LessOrEqual(modifier, 1.2f); // Clamped
        }
        
        [Test]
        public void PatientProfile_GetSmokingCapacityModifier_NonSmoker()
        {
            var patient = new PatientProfile(60, false, 0, DietType.Normal);
            
            float modifier = patient.GetSmokingCapacityModifier();
            
            Assert.AreEqual(1.0f, modifier, 0.001f);
        }
        
        [Test]
        public void PatientProfile_GetSmokingCapacityModifier_LightSmoker()
        {
            var patient = new PatientProfile(60, true, 10, DietType.Normal);
            
            float modifier = patient.GetSmokingCapacityModifier();
            
            // 1 - 0.003*10 = 0.97
            Assert.AreEqual(0.97f, modifier, 0.01f);
        }
        
        [Test]
        public void PatientProfile_GetSmokingCapacityModifier_HeavySmoker()
        {
            var patient = new PatientProfile(60, true, 50, DietType.Normal);
            
            float modifier = patient.GetSmokingCapacityModifier();
            
            // 1 - 0.003*50 = 0.85
            Assert.AreEqual(0.85f, modifier, 0.01f);
        }
        
        [Test]
        public void PatientProfile_GetSmokingCapacityModifier_ClampedMin()
        {
            var patient = new PatientProfile(60, true, 100, DietType.Normal);
            
            float modifier = patient.GetSmokingCapacityModifier();
            
            Assert.GreaterOrEqual(modifier, 0.7f); // Clamped
        }
        
        [Test]
        public void PatientProfile_GetDietModifier_Saludable()
        {
            var patient = new PatientProfile(60, false, 0, DietType.Saludable);
            
            float modifier = patient.GetDietModifier();
            
            Assert.AreEqual(0.9f, modifier, 0.001f);
        }
        
        [Test]
        public void PatientProfile_GetDietModifier_Normal()
        {
            var patient = new PatientProfile(60, false, 0, DietType.Normal);
            
            float modifier = patient.GetDietModifier();
            
            Assert.AreEqual(1.0f, modifier, 0.001f);
        }
        
        [Test]
        public void PatientProfile_GetDietModifier_Mala()
        {
            var patient = new PatientProfile(60, false, 0, DietType.Mala);
            
            float modifier = patient.GetDietModifier();
            
            Assert.AreEqual(1.1f, modifier, 0.001f);
        }
        
        [Test]
        public void PatientProfile_Validate_ValidProfile()
        {
            var patient = new PatientProfile(60, true, 30, DietType.Normal);
            
            bool isValid = patient.Validate();
            
            Assert.IsTrue(isValid);
        }
        
        [Test]
        public void PatientProfile_Validate_NegativeAge()
        {
            var patient = new PatientProfile(-5, false, 0, DietType.Normal);
            
            bool isValid = patient.Validate();
            
            Assert.IsFalse(isValid);
        }
        
        [Test]
        public void PatientProfile_Validate_TooOld()
        {
            var patient = new PatientProfile(121, false, 0, DietType.Normal);
            
            bool isValid = patient.Validate();
            
            Assert.IsFalse(isValid);
        }
        
        [Test]
        public void PatientProfile_Validate_NegativePackYears()
        {
            var patient = new PatientProfile(60, true, -10, DietType.Normal);
            
            bool isValid = patient.Validate();
            
            Assert.IsFalse(isValid);
        }
        
        [Test]
        public void PatientProfile_Validate_TooMuchPackYears()
        {
            var patient = new PatientProfile(60, true, 200, DietType.Normal);
            
            bool isValid = patient.Validate();
            
            Assert.IsFalse(isValid);
        }
        
        [Test]
        public void PatientProfile_Validate_SmokingInconsistency()
        {
            // No fumador pero con pack-years
            var patient = new PatientProfile(60, false, 20, DietType.Normal);
            
            bool isValid = patient.Validate();
            
            Assert.IsFalse(isValid);
        }
        
        [Test]
        public void PatientProfile_GetCombinedModifier_MultipliesAll()
        {
            var patient = new PatientProfile(70, true, 40, DietType.Mala);
            
            float ageModifier = patient.GetAgeGrowthModifier(); // ~1.1
            float smokingModifier = patient.GetSmokingCapacityModifier(); // ~0.88
            float dietModifier = patient.GetDietModifier(); // 1.1
            
            float combined = ageModifier * smokingModifier * dietModifier;
            
            // Verificar que todos los modificadores se aplican
            Assert.Greater(combined, 0.5f);
            Assert.Less(combined, 2.0f);
        }
        
        [Test]
        public void PatientProfile_ToString_ContainsInfo()
        {
            var patient = new PatientProfile(65, true, 30, DietType.Saludable);
            
            string str = patient.ToString();
            
            Assert.IsTrue(str.Contains("65"));
            Assert.IsTrue(str.Contains("fumador") || str.Contains("Fumador"));
        }
    }
}
