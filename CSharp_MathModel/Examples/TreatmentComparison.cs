/*
 * TreatmentComparison.cs
 * Comparación de diferentes tratamientos
 * 
 * Muestra: Evolución con quimioterapia, radioterapia e inmunoterapia
 */

using System;
using System.Collections.Generic;
using LungCancerVR.MathModel;

namespace LungCancerVR.Examples
{
    class TreatmentComparison
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== LungCancerVR: Comparación de Tratamientos ===\n");
            
            // Paciente con tumor avanzado
            var patient = new PatientProfile(
                age: 62,
                isSmoker: true,
                packYears: 40,
                diet: DietType.Poor
            );
            
            Console.WriteLine($"Paciente: {patient}\n");
            
            // Condiciones iniciales (Estadio IIIA)
            float initialSensitive = 80.0f;
            float initialResistant = 20.0f;
            
            Console.WriteLine($"Tumor inicial: {initialSensitive + initialResistant:F2} cm³");
            Console.WriteLine($"Fracción resistente: {20.0f / 100.0f * 100:F1}%\n");
            
            // Simular cada tratamiento
            var treatments = new List<TreatmentType>
            {
                TreatmentType.None,
                TreatmentType.Chemotherapy,
                TreatmentType.Radiotherapy,
                TreatmentType.Immunotherapy
            };
            
            var results = new Dictionary<TreatmentType, (float finalTotal, float finalResistance)>();
            
            foreach (var treatment in treatments)
            {
                var model = new TumorGrowthModel(patient);
                model.SetInitialConditions(initialSensitive, initialResistant);
                model.SetTreatment(treatment);
                
                Console.WriteLine($"--- {GetTreatmentName(treatment)} ---");
                Console.WriteLine("Día\tTotal (cm³)\tSensibles\tResistentes\tFrac.Res.(%)");
                Console.WriteLine("---\t-----------\t---------\t-----------\t------------");
                
                // Simular 60 días
                for (int day = 0; day <= 60; day += 15)
                {
                    float resistanceFraction = model.GetResistanceFraction();
                    Console.WriteLine($"{day}\t{model.TotalCells:F2}\t\t{model.SensitiveCells:F2}\t\t{model.ResistantCells:F2}\t\t{resistanceFraction * 100:F1}");
                    
                    // Simular 15 días
                    for (int i = 0; i < 15; i++)
                    {
                        model.Simulate(1.0f);
                    }
                }
                
                results[treatment] = (model.TotalCells, model.GetResistanceFraction());
                Console.WriteLine($"Final: {model.TotalCells:F2} cm³, Resistencia: {model.GetResistanceFraction() * 100:F1}%\n");
            }
            
            // Análisis comparativo
            Console.WriteLine("\n=== ANÁLISIS COMPARATIVO ===");
            Console.WriteLine("Tratamiento\t\t\tVolumen Final\tReducción\tResistencia");
            Console.WriteLine("-----------\t\t\t-------------\t---------\t-----------");
            
            float baselineVolume = results[TreatmentType.None].finalTotal;
            
            foreach (var treatment in treatments)
            {
                var (finalTotal, finalResistance) = results[treatment];
                float reduction = ((baselineVolume - finalTotal) / baselineVolume) * 100;
                
                string treatmentName = GetTreatmentName(treatment).PadRight(20);
                Console.WriteLine($"{treatmentName}\t{finalTotal:F2} cm³\t{reduction:F1}%\t\t{finalResistance * 100:F1}%");
            }
            
            // Recomendaciones
            Console.WriteLine("\n=== RECOMENDACIONES ===");
            
            var chemoResult = results[TreatmentType.Chemotherapy];
            var radioResult = results[TreatmentType.Radiotherapy];
            var immunoResult = results[TreatmentType.Immunotherapy];
            
            if (chemoResult.finalTotal < radioResult.finalTotal)
            {
                Console.WriteLine("✓ Quimioterapia muestra mejor reducción inicial");
            }
            else
            {
                Console.WriteLine("✓ Radioterapia muestra mejor respuesta local");
            }
            
            if (immunoResult.finalResistance < chemoResult.finalResistance)
            {
                Console.WriteLine("✓ Inmunoterapia reduce desarrollo de resistencia");
            }
            
            if (chemoResult.finalResistance > 0.5f)
            {
                Console.WriteLine("⚠️ Alta resistencia con quimio - considerar terapia combinada");
            }
            
            Console.WriteLine("\nPresiona cualquier tecla para salir...");
            Console.ReadKey();
        }
        
        static string GetTreatmentName(TreatmentType treatment)
        {
            return treatment switch
            {
                TreatmentType.None => "Sin tratamiento",
                TreatmentType.Chemotherapy => "Quimioterapia",
                TreatmentType.Radiotherapy => "Radioterapia",
                TreatmentType.Immunotherapy => "Inmunoterapia",
                _ => "Desconocido"
            };
        }
    }
}
