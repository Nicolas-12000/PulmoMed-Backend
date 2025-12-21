"""
LLM Client - Ollama Integration (Plug-in)
Placeholder mock hasta tener GPU disponible
"""

from app.core.config import get_settings


class OllamaClient:
    """
    Cliente para Ollama LLM (SOLID: Single Responsibility)
    Actualmente retorna respuestas mock educativas
    """

    def __init__(self):
        self.settings = get_settings()
        self.is_available = False  # Cambiar a True cuando Ollama esté listo

    def query(self, prompt: str) -> str:
        """
        Envía prompt al LLM y retorna respuesta

        MOCK ACTUAL: Respuesta educativa genérica
        FUTURO (con Ollama):
            from langchain_community.llms import Ollama
            llm = Ollama(
                base_url=self.settings.ollama_base_url,
                model=self.settings.ollama_model,
                temperature=self.settings.ollama_temperature
            )
            return llm.invoke(prompt)
        """
        if not self.is_available:
            return self._mock_response(prompt)

        # TODO: Implementar cuando Ollama esté disponible
        raise NotImplementedError("Ollama no está configurado aún")

    def _mock_response(self, prompt: str) -> str:
        """
        Respuesta mock educativa mientras no haya GPU
        Simula un LLM médico bien calibrado
        """
        # Detectar tipo de consulta en el prompt
        if "tratamiento" in prompt.lower():
            return (
                "**Explicación del Estado Actual:**\n\n"
                "El tumor ha alcanzado un volumen que requiere intervención "
                "terapéutica. Las células cancerosas siguen un crecimiento "
                "gompertziano, donde la tasa de crecimiento disminuye a medida "
                "que el tumor se acerca a la capacidad de carga del tejido "
                "pulmonar.\n\n"
                "**Recomendación Educativa:**\n\n"
                "En casos similares según NCCN Guidelines 2024:\n"
                "- **Estadio I-II**: Resección quirúrgica seguida de quimioterapia "
                "adyuvante (cisplatino + pemetrexed)\n"
                "- **Estadio III**: Quimiorradioterapia concurrente + inmunoterapia "
                "de consolidación (durvalumab)\n"
                "- **Estadio IV**: Inmunoterapia (pembrolizumab) o terapia dirigida "
                "según mutaciones\n\n"
                "**Factores de Riesgo Detectados:**\n"
                "El tabaquismo (pack-years elevado) incrementa la probabilidad "
                "de resistencia a tratamientos. La progresión puede seguir "
                "patrones de resistencia adquirida.\n\n"
                "**Disclaimer:** Esta es una simulación educativa. Las decisiones "
                "clínicas reales requieren biopsia, estadificación TNM completa, y "
                "análisis molecular (EGFR, ALK, ROS1, PD-L1)."
            )

        if "progresión" in prompt.lower() or "volumen" in prompt.lower():
            return (
                "**Análisis de Progresión Tumoral:**\n\n"
                "El modelo matemático (Gompertz modificado) muestra que el "
                "tumor está en fase de crecimiento exponencial temprano. La "
                "tasa de duplicación actual sugiere un tiempo de duplicación de "
                "aprox. 120-180 días, consistente con adenocarcinomas pulmonares.\n\n"
                "**Mecanismo Biológico:**\n"
                "- Las células sensibles dominan el volumen total\n"
                "- La angiogénesis tumoral está activa (necesaria para volúmenes "
                ">0.5 cm³)\n"
                "- La hipoxia central puede estar desarrollándose, favoreciendo "
                "resistencia\n\n"
                "**Interpretación Educativa:**\n"
                "Este patrón de crecimiento es típico en NSCLC sin tratamiento. "
                "La intervención temprana (estadios I-II) tiene tasas de "
                "supervivencia a 5 años del 60-80%, mientras que estadios "
                "avanzados caen a 10-15%.\n\n"
                "**Fuente:** SEER Database 2015-2020, NCCN NSCLC Guidelines v3.2024"
            )

        # Default general analysis
        return (
            "**Análisis General del Caso:**\n\n"
            "La simulación refleja un caso de cáncer de pulmón no microcítico (NSCLC) "
            "con parámetros realistas basados en datos epidemiológicos. El modelo "
            "considera:\n\n"
            "1. **Factores de Riesgo:** Edad, tabaquismo, dieta y predisposición "
            "genética\n"
            "2. **Dinámica Tumoral:** Crecimiento gompertziano con dos poblaciones "
            "(sensibles/resistentes)\n"
            "3. **Respuesta a Tratamiento:** Eficacia dependiente del tipo de "
            "terapia y resistencia\n\n"
            "**Objetivo Educativo:**\n"
            "Comprender cómo los factores del paciente influyen en la progresión y "
            "respuesta terapéutica. Las decisiones clínicas deben basarse en "
            "evidencia (guías NCCN) y análisis molecular individualizado.\n\n"
            "**Nota Importante:** Este simulador tiene fines educativos únicamente. "
            "No sustituye el criterio clínico ni las pruebas diagnósticas reales."
        )

    def check_availability(self) -> bool:
        """Verifica si Ollama está disponible"""
        return self.is_available
