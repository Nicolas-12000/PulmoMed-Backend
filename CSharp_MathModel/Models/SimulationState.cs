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
        public int Edad { get; set; }
        
        [JsonPropertyName("es_fumador")]
        public bool EsFumador { get; set; }
        
        [JsonPropertyName("pack_years")]
        public float PackYears { get; set; }
        
        [JsonPropertyName("dieta")]
        public string Dieta { get; set; } // "saludable", "normal", "mala"
        
        // Estado del Tumor
        [JsonPropertyName("volumen_tumor_sensible")]
        public float VolumenTumorSensible { get; set; }
        
        [JsonPropertyName("volumen_tumor_resistente")]
        public float VolumenTumorResistente { get; set; }
        
        // Tratamiento
        [JsonPropertyName("tratamiento_activo")]
        public string TratamientoActivo { get; set; } // "ninguno", "quimio", "radio", "inmuno"
        
        [JsonPropertyName("dias_tratamiento")]
        public int DiasTratamiento { get; set; }
        
        // Contexto
        [JsonPropertyName("modo")]
        public string Modo { get; set; } // "libre", "biblioteca"
        
        [JsonPropertyName("caso_id")]
        public string CasoId { get; set; }
        
        /// <summary>
        /// Constructor por defecto
        /// </summary>
        public SimulationState()
        {
            Edad = 60;
            EsFumador = false;
            PackYears = 0.0f;
            Dieta = "normal";
            VolumenTumorSensible = 0.0f;
            VolumenTumorResistente = 0.0f;
            TratamientoActivo = "ninguno";
            DiasTratamiento = 0;
            Modo = "libre";
            CasoId = null;
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
                Edad = patient.Edad,
                EsFumador = patient.EsFumador,
                PackYears = patient.PackYears,
                Dieta = DietTypeToString(patient.Dieta),
                VolumenTumorSensible = model.SensitiveCells,
                VolumenTumorResistente = model.ResistantCells,
                TratamientoActivo = "ninguno", // Debe ser actualizado externamente
                DiasTratamiento = (int)model.CurrentTime,
                Modo = "libre"
            };
        }
        
        /// <summary>
        /// Volumen total del tumor
        /// </summary>
        [JsonIgnore]
        public float VolumenTotal => VolumenTumorSensible + VolumenTumorResistente;
        
        /// <summary>
        /// Convierte DietType a string para JSON
        /// </summary>
        private static string DietTypeToString(DietType diet)
        {
            return diet switch
            {
                DietType.Saludable => "saludable",
                DietType.Normal => "normal",
                DietType.Mala => "mala",
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
                "saludable" => DietType.Saludable,
                "normal" => DietType.Normal,
                "mala" => DietType.Mala,
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
            return $"SimulationState: Paciente {Edad} años, Tumor: {VolumenTotal:F2} cm³, " +
                   $"Tratamiento: {TratamientoActivo}";
        }
    }
    
    /// <summary>
    /// Respuesta del backend (TeacherResponse)
    /// </summary>
    [Serializable]
    public class TeacherResponse
    {
        [JsonPropertyName("explicacion")]
        public string Explicacion { get; set; }
        
        [JsonPropertyName("recomendacion")]
        public string Recomendacion { get; set; }
        
        [JsonPropertyName("fuentes")]
        public string[] Fuentes { get; set; }
        
        [JsonPropertyName("advertencia")]
        public string Advertencia { get; set; }
        
        [JsonPropertyName("retrieved_chunks")]
        public int RetrievedChunks { get; set; }
        
        [JsonPropertyName("llm_model")]
        public string LlmModel { get; set; }
        
        public TeacherResponse()
        {
            Fuentes = Array.Empty<string>();
        }
    }
}
