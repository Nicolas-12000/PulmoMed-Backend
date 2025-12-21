/*
 * PatientProfile.cs
 * Perfil del paciente con factores de riesgo que modifican la progresión tumoral
 * 
 * Factores implementados según literatura médica:
 * - Edad: Afecta tasa de crecimiento (r_s)
 * - Tabaquismo: Afecta capacidad de carga (K)
 * - Dieta: Modificador general de progresión
 * - Genética: Predisposición heredada
 */

using System;

namespace LungCancerVR.MathModel
{
    /// <summary>
    /// Representa el perfil clínico de un paciente
    /// </summary>
    [Serializable]
    public class PatientProfile
    {
        // Datos demográficos
        public int Edad { get; set; }
        public bool EsFumador { get; set; }
        public float PackYears { get; set; }  // Paquetes-año acumulados
        
        // Factores de estilo de vida
        public DietType Dieta { get; set; }
        
        // Predisposición genética (0.8 = baja, 1.0 = normal, 1.2 = alta)
        public float FactorGenetico { get; set; } = 1.0f;
        
        // Constructores
        public PatientProfile()
        {
            Edad = 60;
            EsFumador = false;
            PackYears = 0.0f;
            Dieta = DietType.Normal;
            FactorGenetico = 1.0f;
        }
        
        public PatientProfile(int edad, bool esFumador, float packYears, DietType dieta, float factorGenetico = 1.0f)
        {
            Edad = edad;
            EsFumador = esFumador;
            PackYears = packYears;
            Dieta = dieta;
            FactorGenetico = factorGenetico;
        }
        
        /// <summary>
        /// Calcula el modificador de la tasa de crecimiento basado en edad
        /// Fórmula: r_s = r_base * (1 + 0.005 * (edad - 50))
        /// Pacientes mayores tienen tumores ligeramente más agresivos
        /// </summary>
        public float GetAgeGrowthModifier()
        {
            return 1.0f + 0.005f * (Edad - 50);
        }
        
        /// <summary>
        /// Calcula el modificador de capacidad de carga basado en tabaquismo
        /// Fórmula: K = K_base * (1 - 0.003 * pack_years)
        /// Tabaquismo reduce capacidad tisular por daño pulmonar
        /// </summary>
        public float GetSmokingCapacityModifier()
        {
            if (!EsFumador && PackYears == 0)
                return 1.0f;
            
            float modifier = 1.0f - 0.003f * PackYears;
            return Math.Max(0.5f, modifier); // Mínimo 50% capacidad
        }
        
        /// <summary>
        /// Calcula el modificador de dieta
        /// Dieta saludable ralentiza progresión ligeramente
        /// </summary>
        public float GetDietModifier()
        {
            return Dieta switch
            {
                DietType.Saludable => 0.90f,  // -10% progresión
                DietType.Normal => 1.0f,
                DietType.Mala => 1.10f,        // +10% progresión
                _ => 1.0f
            };
        }
        
        /// <summary>
        /// Calcula el modificador combinado de todos los factores
        /// Usado para ajustar tasas de crecimiento global
        /// </summary>
        public float GetCombinedModifier()
        {
            return GetAgeGrowthModifier() * 
                   GetSmokingCapacityModifier() * 
                   GetDietModifier() * 
                   FactorGenetico;
        }
        
        /// <summary>
        /// Valida que los valores del perfil sean realistas
        /// </summary>
        public bool IsValid(out string errorMessage)
        {
            if (Edad < 18 || Edad > 120)
            {
                errorMessage = "Edad debe estar entre 18 y 120 años";
                return false;
            }
            
            if (PackYears < 0 || PackYears > 150)
            {
                errorMessage = "Pack-years debe estar entre 0 y 150";
                return false;
            }
            
            if (!EsFumador && PackYears > 0)
            {
                errorMessage = "Pack-years debe ser 0 si no es fumador";
                return false;
            }
            
            if (FactorGenetico < 0.5f || FactorGenetico > 2.0f)
            {
                errorMessage = "Factor genético debe estar entre 0.5 y 2.0";
                return false;
            }
            
            errorMessage = string.Empty;
            return true;
        }
        
        public override string ToString()
        {
            return $"Paciente: {Edad} años, Fumador: {EsFumador}, " +
                   $"Pack-years: {PackYears:F1}, Dieta: {Dieta}, " +
                   $"Factor genético: {FactorGenetico:F2}";
        }
    }
    
    /// <summary>
    /// Tipo de dieta del paciente
    /// </summary>
    public enum DietType
    {
        Saludable,  // Rica en frutas, verduras, baja en procesados
        Normal,     // Dieta promedio
        Mala        // Alta en procesados, baja en nutrientes
    }
}
