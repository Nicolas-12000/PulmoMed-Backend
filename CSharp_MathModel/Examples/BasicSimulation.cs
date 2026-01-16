/*
 * BasicSimulation.cs
 * Ejemplo básico de uso del modelo matemático
 * 
 * Muestra: Creación de paciente, tumor inicial, simulación sin tratamiento
 */

using System;
using LungCancerVR.MathModel;

namespace LungCancerVR.Examples
{
    class BasicSimulation
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== LungCancerVR: Simulación Básica ===\n");
            
            // 1. Crear perfil de paciente
            var patient = new PatientProfile(
                age: 65,
                isSmoker: true,
                packYears: 30,
                diet: DietType.Normal
            );
            
            Console.WriteLine($"Paciente: {patient}");
            Console.WriteLine($"Modificador edad: {patient.GetAgeGrowthModifier():F3}");
            Console.WriteLine($"Modificador tabaco: {patient.GetSmokingCapacityModifier():F3}");
            Console.WriteLine();
            
            // 2. Crear modelo de crecimiento tumoral
            var model = new TumorGrowthModel(patient);
            
            // 3. Establecer condiciones iniciales (Estadio IA detectado)
            float initialSensitive = 5.0f;  // 5 cm³ células sensibles
            float initialResistant = 0.5f;  // 0.5 cm³ células resistentes
            
            model.SetInitialConditions(initialSensitive, initialResistant);
            
            Console.WriteLine($"Tumor inicial: {model.TotalCells:F2} cm³");
            Console.WriteLine($"Estadio aproximado: {model.GetApproximateStage()}");
            Console.WriteLine($"Tiempo de duplicación: {model.GetDoublingTime():F1} días");
            Console.WriteLine($"Fracción resistente: {model.GetResistanceFraction() * 100:F1}%");
            Console.WriteLine();
            
            // 4. Simular progresión sin tratamiento (90 días)
            Console.WriteLine("Simulando 90 días sin tratamiento...\n");
            Console.WriteLine("Día\tTotal (cm³)\tSensibles\tResistentes\tEstadio");
            Console.WriteLine("---\t-----------\t---------\t-----------\t-------");
            
            for (int day = 0; day <= 90; day += 10)
            {
                Console.WriteLine($"{day}\t{model.TotalCells:F2}\t\t{model.SensitiveCells:F2}\t\t{model.ResistantCells:F2}\t\t{model.GetApproximateStage()}");
                
                // Simular 10 días
                for (int i = 0; i < 10; i++)
                {
                    model.Simulate(1.0f);
                }
            }
            
            Console.WriteLine($"\nFinal: {model.TotalCells:F2} cm³");
            Console.WriteLine($"Estadio final: {model.GetApproximateStage()}");
            Console.WriteLine($"Fracción resistente final: {model.GetResistanceFraction() * 100:F1}%");
            
            // 5. Análisis de velocidad de crecimiento
            float doublingTime = model.GetDoublingTime();
            Console.WriteLine($"\nTiempo de duplicación actual: {doublingTime:F1} días");
            
            if (doublingTime < 50)
            {
                Console.WriteLine("⚠️ Crecimiento muy rápido - Tumor agresivo");
            }
            else if (doublingTime < 90)
            {
                Console.WriteLine("⚠️ Crecimiento moderado - Requiere vigilancia");
            }
            else
            {
                Console.WriteLine("✓ Crecimiento lento - Tumor menos agresivo");
            }
            
            Console.WriteLine("\nPresiona cualquier tecla para salir...");
            Console.ReadKey();
        }
    }
}
