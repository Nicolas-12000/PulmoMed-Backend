/*
 * SimulationState.cs
 * Data Transfer Object (DTO) para comunicación con Python Backend
 * 
 * Mirror exacto de app/models/simulation_state.py (Pydantic)
 * Serializable a JSON para HTTP requests
 */

using System;
using System.Text.Json.Serialization;

namespace LungCancerVR.MathModel
{
    /// <summary>
    /// Estado de la simulación para enviar al backend
    /// Compatible con SimulationState de Python (Pydantic)
    /// </summary>
    [Serializable]
    public class SimulationState
    {
        // Datos del Paciente
        [JsonPropertyName("edad")]
        public int Age { get; set; }
        
        [JsonPropertyName("es_fumador")]
        public bool IsSmoker { get; set; }
        
        [JsonPropertyName("pack_years")]
        public float PackYears { get; set; }
        
        [JsonPropertyName("dieta")]
        public string Diet { get; set; } // "saludable", "normal", "mala"
        
        // Estado del Tumor
        [JsonPropertyName("volumen_tumor_sensible")]
        public float SensitiveTumorVolume { get; set; }
        
        [JsonPropertyName("volumen_tumor_resistente")]
        public float ResistantTumorVolume { get; set; }
        
        // Tratamiento
        [JsonPropertyName("tratamiento_activo")]
        public string ActiveTreatment { get; set; } // "ninguno", "quimio", "radio", "inmuno"
        
        [JsonPropertyName("dias_tratamiento")]
        public int TreatmentDays { get; set; }
        
        // Contexto
        [JsonPropertyName("modo")]
        public string Mode { get; set; } // "libre", "biblioteca"
        
        [JsonPropertyName("caso_id")]
        public string CaseId { get; set; }
        
        /// <summary>
        /// Constructor por defecto
        /// </summary>
        public SimulationState()
        {
            Age = 60;
            IsSmoker = false;
            PackYears = 0.0f;
            Diet = "normal";
            SensitiveTumorVolume = 0.0f;
            ResistantTumorVolume = 0.0f;
            ActiveTreatment = "ninguno";
            TreatmentDays = 0;
            Mode = "libre";
            CaseId = null;
        }
        
        /// <summary>
        /// Crea SimulationState desde TumorGrowthModel
        /// </summary>
        public static SimulationState FromModel(TumorGrowthModel model, PatientProfile patient)
        {
            if (model == null || patient == null)
                throw new ArgumentNullException();
            
            return new SimulationState
            {
                Age = patient.Age,
                IsSmoker = patient.IsSmoker,
                PackYears = patient.PackYears,
                Diet = DietTypeToString(patient.Diet),
                SensitiveTumorVolume = model.SensitiveCells,
                ResistantTumorVolume = model.ResistantCells,
                ActiveTreatment = "ninguno", // Debe ser actualizado externamente
                TreatmentDays = (int)model.CurrentTime,
                Mode = "libre"
            };
        }
        
        /// <summary>
        /// Volumen total del tumor
        /// </summary>
        [JsonIgnore]
        public float TotalVolume => SensitiveTumorVolume + ResistantTumorVolume;
        
        /// <summary>
        /// Convierte DietType a string para JSON
        /// </summary>
        private static string DietTypeToString(DietType diet)
        {
            return diet switch
            {
                DietType.Healthy => "saludable",
                DietType.Normal => "normal",
                DietType.Poor => "mala",
                _ => "normal"
            };
        }
        
        /// <summary>
        /// Convierte string a DietType
        /// </summary>
        public static DietType StringToDietType(string diet)
        {
            return diet?.ToLower() switch
            {
                "saludable" => DietType.Healthy,
                "normal" => DietType.Normal,
                "mala" => DietType.Poor,
                _ => DietType.Normal
            };
        }
        
        /// <summary>
        /// Convierte string a TreatmentType
        /// </summary>
        public static TreatmentType StringToTreatmentType(string treatment)
        {
            return treatment?.ToLower() switch
            {
                "ninguno" => TreatmentType.None,
                "quimio" => TreatmentType.Chemotherapy,
                "radio" => TreatmentType.Radiotherapy,
                "inmuno" => TreatmentType.Immunotherapy,
                _ => TreatmentType.None
            };
        }
        
        public override string ToString()
        {
                 return $"SimulationState: Paciente {Age} años, Tumor: {TotalVolume:F2} cm³, " +
                     $"Tratamiento: {ActiveTreatment}";
        }
    }
    
    /// <summary>
    /// Respuesta del backend (TeacherResponse)
    /// </summary>
    [Serializable]
    public class TeacherResponse
    {
        [JsonPropertyName("explicacion")]
        public string Explanation { get; set; }
        
        [JsonPropertyName("recomendacion")]
        public string Recommendation { get; set; }
        
        [JsonPropertyName("fuentes")]
        public string[] Sources { get; set; }
        
        [JsonPropertyName("advertencia")]
        public string Warning { get; set; }
        
        [JsonPropertyName("retrieved_chunks")]
        public int RetrievedChunks { get; set; }
        
        [JsonPropertyName("llm_model")]
        public string LlmModel { get; set; }
        
        public TeacherResponse()
        {
            Sources = Array.Empty<string>();
        }
    }
}
