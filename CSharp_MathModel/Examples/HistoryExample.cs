/*
 * HistoryExample.cs
 * Ejemplo de uso del sistema de historial tipo Git
 * 
 * Muestra: Snapshots, deltas, rewind, branch, comparación de timelines
 */

using System;
using LungCancerVR.MathModel;

namespace LungCancerVR.Examples
{
    class HistoryExample
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== LungCancerVR: Sistema de Historial Tipo Git ===\n");
            
            // 1. Crear paciente y modelo
            var patient = new PatientProfile(
                edad: 58,
                esFumador: true,
                packYears: 30,
                dieta: DietType.Normal
            );
            
            var model = new TumorGrowthModel(patient);
            model.SetInitialConditions(15.0f, 2.0f); // Estadio IB
            
            Console.WriteLine($"Tumor inicial: {model.TotalCells:F2} cm³");
            Console.WriteLine($"Estadio: {model.GetApproximateStage()}\n");
            
            // 2. Crear sistema de historial
            // Snapshot cada 30 días, máximo 50 deltas entre snapshots
            var history = new SimulationHistory(
                snapshotInterval: 30, 
                maxDeltas: 50
            );
            
            // Inicializar con estado actual
            history.Initialize(model, "none", "Tumor detectado - Estadio IB");
            Console.WriteLine("✓ Historial inicializado\n");
            
            // 3. Simular sin tratamiento por 60 días (observación)
            Console.WriteLine("--- Fase 1: Observación sin tratamiento (60 días) ---");
            
            for (int day = 1; day <= 60; day++)
            {
                model.Simulate(1.0f);
                
                // Guardar estado cada 5 días (crea deltas o snapshots según config)
                if (day % 5 == 0)
                {
                    history.SaveState(model, "none");
                    
                    if (day % 30 == 0)
                    {
                        Console.WriteLine($"Día {day}: {model.TotalCells:F2} cm³ - " +
                                        $"Estadio {model.GetApproximateStage()} " +
                                        $"[Snapshot #{history.TotalSnapshots}]");
                    }
                }
            }
            
            float volumeBeforeTreatment = model.TotalCells;
            string stageBeforeTreatment = model.GetApproximateStage();
            
            Console.WriteLine($"\nDespués de 60 días: {volumeBeforeTreatment:F2} cm³, " +
                            $"Estadio {stageBeforeTreatment}");
            Console.WriteLine($"Memoria usada: {history.GetMemoryUsage()}\n");
            
            // 4. Crear punto de bifurcación (branch) - CHECKPOINT IMPORTANTE
            string checkpointId = history.CreateBranch("tratamiento-quimio");
            history.SaveState(model, "none", forceSnapshot: true);
            
            Console.WriteLine($"✓ Checkpoint creado: {checkpointId}\n");
            
            // 5. Timeline A: Probar quimioterapia
            Console.WriteLine("--- Timeline A: Quimioterapia (90 días) ---");
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            for (int day = 1; day <= 90; day++)
            {
                model.Simulate(1.0f);
                
                if (day % 5 == 0)
                {
                    history.SaveState(model, "quimio");
                }
                
                if (day % 30 == 0)
                {
                    Console.WriteLine($"Día {day}: {model.TotalCells:F2} cm³ - " +
                                    $"Resistencia: {model.GetResistanceFraction() * 100:F1}%");
                }
            }
            
            float volumeAfterChemo = model.TotalCells;
            float resistanceChemo = model.GetResistanceFraction();
            
            Console.WriteLine($"\nResultado Quimio:");
            Console.WriteLine($"  Volumen final: {volumeAfterChemo:F2} cm³");
            Console.WriteLine($"  Resistencia: {resistanceChemo * 100:F1}%");
            Console.WriteLine($"  Cambio: {((volumeAfterChemo - volumeBeforeTreatment) / volumeBeforeTreatment * 100):F1}%\n");
            
            // 6. RETROCEDER en el tiempo al checkpoint
            Console.WriteLine("--- Retrocediendo al checkpoint... ---");
            bool rewound = history.GoToCheckpoint(model, checkpointId);
            
            if (rewound)
            {
                Console.WriteLine($"✓ Restaurado a día 60: {model.TotalCells:F2} cm³");
                Console.WriteLine($"  (Volumen original era: {volumeBeforeTreatment:F2} cm³)\n");
            }
            
            // 7. Timeline B: Probar inmunoterapia desde el mismo punto
            history.CreateBranch("tratamiento-inmuno");
            Console.WriteLine("--- Timeline B: Inmunoterapia (90 días) ---");
            model.SetTreatment(TreatmentType.Immunotherapy);
            
            for (int day = 1; day <= 90; day++)
            {
                model.Simulate(1.0f);
                
                if (day % 5 == 0)
                {
                    history.SaveState(model, "inmuno");
                }
                
                if (day % 30 == 0)
                {
                    Console.WriteLine($"Día {day}: {model.TotalCells:F2} cm³ - " +
                                    $"Resistencia: {model.GetResistanceFraction() * 100:F1}%");
                }
            }
            
            float volumeAfterImmuno = model.TotalCells;
            float resistanceImmuno = model.GetResistanceFraction();
            
            Console.WriteLine($"\nResultado Inmuno:");
            Console.WriteLine($"  Volumen final: {volumeAfterImmuno:F2} cm³");
            Console.WriteLine($"  Resistencia: {resistanceImmuno * 100:F1}%");
            Console.WriteLine($"  Cambio: {((volumeAfterImmuno - volumeBeforeTreatment) / volumeBeforeTreatment * 100):F1}%\n");
            
            // 8. Comparación de resultados
            Console.WriteLine("=== COMPARACIÓN DE TIMELINES ===");
            Console.WriteLine($"Baseline (día 60): {volumeBeforeTreatment:F2} cm³");
            Console.WriteLine();
            Console.WriteLine($"Timeline A (Quimioterapia):");
            Console.WriteLine($"  Final: {volumeAfterChemo:F2} cm³");
            Console.WriteLine($"  Resistencia: {resistanceChemo * 100:F1}%");
            Console.WriteLine();
            Console.WriteLine($"Timeline B (Inmunoterapia):");
            Console.WriteLine($"  Final: {volumeAfterImmuno:F2} cm³");
            Console.WriteLine($"  Resistencia: {resistanceImmuno * 100:F1}%");
            Console.WriteLine();
            
            // 9. Recomendación basada en resultados
            string better = volumeAfterChemo < volumeAfterImmuno ? "Quimioterapia" : "Inmunoterapia";
            float betterVolume = Math.Min(volumeAfterChemo, volumeAfterImmuno);
            float betterResistance = volumeAfterChemo < volumeAfterImmuno ? resistanceChemo : resistanceImmuno;
            
            Console.WriteLine($"✓ Mejor opción: {better}");
            Console.WriteLine($"  Volumen final: {betterVolume:F2} cm³");
            Console.WriteLine($"  Resistencia: {betterResistance * 100:F1}%\n");
            
            // 10. Estadísticas del historial
            Console.WriteLine("=== ESTADÍSTICAS DEL HISTORIAL ===");
            Console.WriteLine($"Snapshots completos: {history.TotalSnapshots}");
            Console.WriteLine($"Deltas incrementales: {history.TotalDeltas}");
            Console.WriteLine($"Memoria total usada: {history.GetMemoryUsage()}");
            
            // Calcular ahorro de memoria
            int totalSteps = 60 + 90 + 90; // 240 pasos
            int stepsRecorded = history.TotalDeltas + history.TotalSnapshots;
            float compressionRatio = (float)stepsRecorded / totalSteps;
            
            Console.WriteLine($"Pasos simulados: {totalSteps}");
            Console.WriteLine($"Pasos guardados: {stepsRecorded}");
            Console.WriteLine($"Ratio de compresión: {compressionRatio:F2}x");
            Console.WriteLine($"Ahorro de memoria: {(1 - compressionRatio) * 100:F1}%\n");
            
            // 11. Listar checkpoints disponibles
            var checkpoints = history.GetCheckpoints();
            Console.WriteLine("=== CHECKPOINTS DISPONIBLES ===");
            
            foreach (var (id, time, description) in checkpoints)
            {
                Console.WriteLine($"[{id}] Día {time:F0}: {description}");
            }
            
            Console.WriteLine("\n✓ Sistema de historial tipo Git funcionando correctamente");
            Console.WriteLine("  - Snapshots + deltas = memoria eficiente");
            Console.WriteLine("  - Rewind/Fast-forward = navegar en el tiempo");
            Console.WriteLine("  - Branching = explorar alternativas sin perder datos");
            
            Console.WriteLine("\nPresiona cualquier tecla para salir...");
            Console.ReadKey();
        }
    }
}
