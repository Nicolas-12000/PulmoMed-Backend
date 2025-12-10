"""
RAG Prompts - Template Management
Prompts reutilizables para el sistema RAG (DRY Principle)
"""


class PromptTemplates:
    """
    Plantillas de prompts para el LLM
    Centralizadas para fácil mantenimiento y A/B testing
    """
    
    SYSTEM_PROMPT = """Eres un asistente de enseñanza médica experto en oncología pulmonar. Tu rol es explicar de forma educativa y precisa la progresión del cáncer de pulmón no microcítico (NSCLC) basándote en:

1. **Modelo matemático**: Ecuaciones de Gompertz modificadas con dos poblaciones
2. **Evidencia médica**: Guías NCCN, datos SEER, estudios clínicos
3. **Contexto del paciente**: Factores de riesgo, tratamientos, y progresión individual

**IMPORTANTE:**
- Usa SOLO la información proporcionada en el contexto médico
- Si no tienes información suficiente, di "No dispongo de información específica sobre..."
- Incluye siempre disclaimers educativos
- Cita las fuentes cuando des recomendaciones

**PROHIBIDO:**
- Dar diagnósticos definitivos
- Recomendar tratamientos como si fuera consulta real
- Inventar datos o estadísticas"""

    TEACHER_QUERY_TEMPLATE = """**Contexto Médico Recuperado:**
{context}

**Estado del Paciente:**
- Edad: {edad} años
- Fumador: {es_fumador} (Pack-years: {pack_years})
- Dieta: {dieta}
- Volumen tumor total: {volumen_total:.2f} cm³ (Sensible: {volumen_sensible:.2f}, Resistente: {volumen_resistente:.2f})
- Estadio aproximado: {estadio}
- Tratamiento activo: {tratamiento}
- Días de tratamiento: {dias_tratamiento}

**Pregunta Educativa:**
Explica de forma clara y educativa:
1. ¿Qué está sucediendo con el tumor en este momento?
2. ¿Qué factores del paciente están influyendo en la progresión?
3. ¿Qué opciones terapéuticas se considerarían según guías NCCN para este estadio?
4. ¿Qué debería aprender el estudiante de este caso?

**Responde en formato:**
- **Explicación:** (mecanismo biológico y matemático)
- **Recomendación:** (opciones según guías, con disclaimer)
- **Fuentes:** (cita específicamente las referencias usadas)"""

    PROGRESSION_ANALYSIS_TEMPLATE = """**Contexto Médico:**
{context}

**Análisis de Progresión:**
El tumor ha evolucionado desde un volumen inicial de {volumen_inicial:.2f} cm³ a {volumen_actual:.2f} cm³ en {dias_simulacion} días.

Tasa de crecimiento observada: {tasa_crecimiento:.3f} cm³/día

**Pregunta:**
Desde una perspectiva educativa, explica:
1. ¿Es esta tasa de crecimiento consistente con NSCLC típico?
2. ¿Qué factores del paciente podrían estar acelerando o ralentizando la progresión?
3. ¿En qué punto se debería intervenir terapéuticamente según guías NCCN?

**Incluye referencias específicas a estudios o estadísticas SEER si están en el contexto.**"""

    TREATMENT_RESPONSE_TEMPLATE = """**Contexto Médico:**
{context}

**Tratamiento Aplicado:**
- Tipo: {tratamiento}
- Duración: {dias_tratamiento} días
- Reducción volumen: {reduccion_porcentaje:.1f}%
- Población resistente: {volumen_resistente:.2f} cm³ ({porcentaje_resistente:.1f}% del total)

**Pregunta Educativa:**
Analiza la respuesta al tratamiento:
1. ¿Es esta reducción consistente con la eficacia esperada de {tratamiento} según ensayos clínicos?
2. ¿La aparición de población resistente es normal? ¿Cuándo ocurre típicamente?
3. ¿Qué estrategias se usan para manejar resistencia según NCCN Guidelines?
4. ¿Qué debería monitorear un clínico en casos similares?

**Usa datos específicos del contexto para fundamentar tu respuesta.**"""

    @staticmethod
    def format_context(chunks: list[dict]) -> str:
        """
        Formatea chunks recuperados en contexto legible para el LLM
        
        Args:
            chunks: Lista de dicts con {text, metadata, distance}
        
        Returns:
            String formateado con el contexto médico
        """
        if not chunks:
            return "No se encontró información médica específica en la base de conocimiento."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "Fuente desconocida")
            text = chunk["text"]
            context_parts.append(f"[Fuente {i}: {source}]\n{text}\n")
        
        return "\n---\n".join(context_parts)
    
    @staticmethod
    def build_teacher_prompt(state: dict, context_chunks: list[dict]) -> str:
        """
        Construye el prompt completo para consulta al profesor
        
        Args:
            state: Dict con estado de simulación (SimulationState.dict())
            context_chunks: Chunks recuperados del RAG
        
        Returns:
            Prompt completo formateado
        """
        context = PromptTemplates.format_context(context_chunks)
        
        return PromptTemplates.TEACHER_QUERY_TEMPLATE.format(
            context=context,
            edad=state["edad"],
            es_fumador="Sí" if state["es_fumador"] else "No",
            pack_years=state["pack_years"],
            dieta=state["dieta"],
            volumen_total=state["volumen_tumor_sensible"] + state["volumen_tumor_resistente"],
            volumen_sensible=state["volumen_tumor_sensible"],
            volumen_resistente=state["volumen_tumor_resistente"],
            estadio=state.get("estadio_aproximado", "No calculado"),
            tratamiento=state["tratamiento_activo"],
            dias_tratamiento=state.get("dias_tratamiento", 0)
        )
