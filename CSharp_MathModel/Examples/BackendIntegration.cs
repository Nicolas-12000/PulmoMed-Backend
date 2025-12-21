/*
 * BackendIntegration.cs
 * Ejemplo de integración con el backend Python (FastAPI)
 * 
 * Muestra: Serialización SimulationState, HTTP request, parsing respuesta
 */

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using LungCancerVR.MathModel;

namespace LungCancerVR.Examples
{
    class BackendIntegration
    {
        private static readonly HttpClient client = new HttpClient();
        private const string BACKEND_URL = "http://localhost:8000";
        
        static async Task Main(string[] args)
        {
            Console.WriteLine("=== LungCancerVR: Integración con Backend ===\n");
            
            // 1. Crear simulación local
            var patient = new PatientProfile(
                edad: 58,
                esFumador: true,
                packYears: 25,
                dieta: DietType.Normal
            );
            
            var model = new TumorGrowthModel(patient);
            model.SetInitialConditions(15.0f, 3.0f); // Estadio IB
            model.SetTreatment(TreatmentType.Chemotherapy);
            
            Console.WriteLine($"Paciente: {patient}");
            Console.WriteLine($"Tumor inicial: {model.TotalCells:F2} cm³");
            Console.WriteLine($"Estadio: {model.GetApproximateStage()}");
            Console.WriteLine($"Tratamiento: Quimioterapia\n");
            
            // 2. Simular 30 días
            Console.WriteLine("Simulando 30 días...");
            for (int i = 0; i < 30; i++)
            {
                model.Simulate(1.0f);
            }
            
            Console.WriteLine($"Tumor después de 30 días: {model.TotalCells:F2} cm³");
            Console.WriteLine($"Estadio actual: {model.GetApproximateStage()}\n");
            
            // 3. Crear SimulationState para enviar al backend
            var simulationState = SimulationState.FromModel(model, patient);
            simulationState.TratamientoActivo = "quimio";
            simulationState.Modo = "libre";
            
            Console.WriteLine("Estado de simulación:");
            Console.WriteLine(JsonSerializer.Serialize(simulationState, new JsonSerializerOptions 
            { 
                WriteIndented = true 
            }));
            Console.WriteLine();
            
            // 4. Consultar al profesor AI (backend)
            Console.WriteLine("Consultando al Profesor AI...\n");
            
            try
            {
                var response = await ConsultarProfesorIA(simulationState);
                
                if (response != null)
                {
                    Console.WriteLine("=== RESPUESTA DEL PROFESOR IA ===");
                    Console.WriteLine($"\nExplicación:\n{response.Explicacion}\n");
                    Console.WriteLine($"Recomendación:\n{response.Recomendacion}\n");
                    
                    if (response.Fuentes != null && response.Fuentes.Length > 0)
                    {
                        Console.WriteLine("Fuentes consultadas:");
                        foreach (var fuente in response.Fuentes)
                        {
                            Console.WriteLine($"  - {fuente}");
                        }
                        Console.WriteLine();
                    }
                    
                    if (!string.IsNullOrEmpty(response.Advertencia))
                    {
                        Console.WriteLine($"⚠️ Advertencia: {response.Advertencia}\n");
                    }
                    
                    Console.WriteLine($"Chunks RAG: {response.RetrievedChunks}");
                    Console.WriteLine($"Modelo LLM: {response.LlmModel}");
                }
            }
            catch (HttpRequestException e)
            {
                Console.WriteLine($"❌ Error de conexión: {e.Message}");
                Console.WriteLine("Verifica que el backend esté corriendo en http://localhost:8000");
            }
            catch (Exception e)
            {
                Console.WriteLine($"❌ Error: {e.Message}");
            }
            
            Console.WriteLine("\nPresiona cualquier tecla para salir...");
            Console.ReadKey();
        }
        
        /// <summary>
        /// Consulta al endpoint /api/profesor/consultar
        /// </summary>
        static async Task<TeacherResponse> ConsultarProfesorIA(SimulationState state)
        {
            var json = JsonSerializer.Serialize(state);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await client.PostAsync(
                $"{BACKEND_URL}/api/profesor/consultar",
                content
            );
            
            response.EnsureSuccessStatusCode();
            
            var responseJson = await response.Content.ReadAsStringAsync();
            var teacherResponse = JsonSerializer.Deserialize<TeacherResponse>(responseJson);
            
            return teacherResponse;
        }
        
        /// <summary>
        /// Obtiene casos de la biblioteca
        /// </summary>
        static async Task ListarCasosBiblioteca()
        {
            var response = await client.GetAsync($"{BACKEND_URL}/api/profesor/casos");
            response.EnsureSuccessStatusCode();
            
            var json = await response.Content.ReadAsStringAsync();
            Console.WriteLine("Casos disponibles:");
            Console.WriteLine(json);
        }
    }
}
