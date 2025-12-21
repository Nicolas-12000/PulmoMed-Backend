/*
 * ITreatmentStrategy.cs
 * Strategy Pattern para diferentes modalidades de tratamiento oncológico
 * 
 * Permite implementar diferentes β(t) (eficacia del tratamiento en el tiempo)
 * sin modificar el modelo de crecimiento tumoral
 * 
 * SOLID: Open/Closed Principle - fácil añadir nuevos tratamientos
 */

using System;

namespace LungCancerVR.MathModel
{
    /// <summary>
    /// Interfaz para estrategias de tratamiento
    /// </summary>
    public interface ITreatmentStrategy
    {
        /// <summary>
        /// Nombre del tratamiento
        /// </summary>
        string Name { get; }
        
        /// <summary>
        /// Calcula la intensidad del tratamiento β(t) en el tiempo t
        /// β(t) representa la tasa de eliminación de células sensibles
        /// </summary>
        /// <param name="time">Tiempo desde inicio del tratamiento (días)</param>
        /// <returns>Intensidad β(t) ∈ [0, 1]</returns>
        float GetBeta(float time);
        
        /// <summary>
        /// Duración típica del ciclo de tratamiento (días)
        /// </summary>
        float CycleDuration { get; }
        
        /// <summary>
        /// Eficacia máxima del tratamiento (0-1)
        /// </summary>
        float MaxEfficacy { get; }
    }
    
    /// <summary>
    /// Tratamiento: Sin tratamiento activo
    /// β(t) = 0 (sin eliminación de células)
    /// </summary>
    public class NoTreatmentStrategy : ITreatmentStrategy
    {
        public string Name => "Ninguno";
        public float CycleDuration => 0f;
        public float MaxEfficacy => 0f;
        
        public float GetBeta(float time)
        {
            return 0f;
        }
    }
    
    /// <summary>
    /// Quimioterapia: Cisplatino + Pemetrexed
    /// β(t) = β_max * (1 - exp(-k*t)) * (1 - 0.1*cycle)
    /// 
    /// Modelo: Acumulación gradual + resistencia progresiva
    /// Basado en: NCCN Guidelines 2024, estudios farmacocinéticos
    /// </summary>
    public class ChemotherapyStrategy : ITreatmentStrategy
    {
        public string Name => "Quimioterapia (Cisplatino + Pemetrexed)";
        public float CycleDuration => 21f; // Ciclos cada 3 semanas
        public float MaxEfficacy => 0.75f; // 75% eficacia máxima
        
        private float betaMax = 0.75f;      // Eficacia máxima
        private float k = 0.15f;            // Tasa de acumulación
        private int currentCycle = 0;
        
        public ChemotherapyStrategy(float betaMax = 0.75f, float accumulationRate = 0.15f)
        {
            this.betaMax = betaMax;
            this.k = accumulationRate;
        }
        
        public float GetBeta(float time)
        {
            // Ciclo actual (cada 21 días)
            currentCycle = (int)(time / CycleDuration);
            
            // Tiempo dentro del ciclo actual
            float timeInCycle = time % CycleDuration;
            
            // Acumulación exponencial dentro del ciclo
            float accumulation = 1.0f - (float)Math.Exp(-k * timeInCycle);
            
            // Reducción por resistencia adquirida (10% por ciclo, máx 50%)
            float resistanceFactor = Math.Max(0.5f, 1.0f - 0.1f * currentCycle);
            
            return betaMax * accumulation * resistanceFactor;
        }
    }
    
    /// <summary>
    /// Radioterapia: Radiación ionizante fraccionada
    /// β(t) = β_max * sin²(π*t/T) si t < T, sino decae exponencialmente
    /// 
    /// Modelo: Picos durante sesiones + efecto residual
    /// Basado en: Estudios radiobiológicos, fraccionamiento estándar
    /// </summary>
    public class RadiotherapyStrategy : ITreatmentStrategy
    {
        public string Name => "Radioterapia (SBRT)";
        public float CycleDuration => 14f; // 2 semanas de tratamiento
        public float MaxEfficacy => 0.85f; // 85% eficacia máxima
        
        private float betaMax = 0.85f;
        private float treatmentDuration = 14f; // Días de tratamiento activo
        private float decayRate = 0.1f;        // Decaimiento post-tratamiento
        
        public RadiotherapyStrategy(float betaMax = 0.85f, float duration = 14f)
        {
            this.betaMax = betaMax;
            this.treatmentDuration = duration;
        }
        
        public float GetBeta(float time)
        {
            if (time < treatmentDuration)
            {
                // Durante tratamiento: picos sinusoidales (sesiones diarias)
                float sinComponent = (float)Math.Sin(Math.PI * time / treatmentDuration);
                return betaMax * sinComponent * sinComponent;
            }
            else
            {
                // Post-tratamiento: decaimiento exponencial del efecto residual
                float timeSinceEnd = time - treatmentDuration;
                float residual = (float)Math.Exp(-decayRate * timeSinceEnd);
                return betaMax * 0.3f * residual; // 30% eficacia residual máxima
            }
        }
    }
    
    /// <summary>
    /// Inmunoterapia: Pembrolizumab (anti-PD-L1)
    /// β(t) = β_max * (1 / (1 + exp(-k*(t - t0)))) si PD-L1 ≥ 50%
    /// 
    /// Modelo: Activación lenta + efecto sostenido
    /// Basado en: KEYNOTE-024, respuestas duraderas en PD-L1 alto
    /// </summary>
    public class ImmunotherapyStrategy : ITreatmentStrategy
    {
        public string Name => "Inmunoterapia (Pembrolizumab)";
        public float CycleDuration => 21f; // Ciclos cada 3 semanas
        public float MaxEfficacy => 0.65f; // 65% eficacia (pero sostenida)
        
        private float betaMax = 0.65f;
        private float k = 0.08f;           // Tasa de activación inmune
        private float t0 = 30f;            // Tiempo de activación (30 días)
        
        public ImmunotherapyStrategy(float betaMax = 0.65f, float activationRate = 0.08f)
        {
            this.betaMax = betaMax;
            this.k = activationRate;
        }
        
        public float GetBeta(float time)
        {
            // Función sigmoide: activación gradual del sistema inmune
            float sigmoid = 1.0f / (1.0f + (float)Math.Exp(-k * (time - t0)));
            
            // Sin pérdida de eficacia (característica de inmunoterapia)
            return betaMax * sigmoid;
        }
    }
    
    /// <summary>
    /// Factory para crear tratamientos
    /// </summary>
    public static class TreatmentFactory
    {
        public static ITreatmentStrategy Create(TreatmentType type)
        {
            return type switch
            {
                TreatmentType.None => new NoTreatmentStrategy(),
                TreatmentType.Chemotherapy => new ChemotherapyStrategy(),
                TreatmentType.Radiotherapy => new RadiotherapyStrategy(),
                TreatmentType.Immunotherapy => new ImmunotherapyStrategy(),
                _ => new NoTreatmentStrategy()
            };
        }
    }
    
    public enum TreatmentType
    {
        None,
        Chemotherapy,
        Radiotherapy,
        Immunotherapy
    }
}
