"""
RAG Prompts - Template Management
Prompts reutilizables para el sistema RAG (DRY Principle)
"""

# flake8: noqa: E501  # Long prompt templates; keep readability over line-length here


class PromptTemplates:
    """
    Plantillas de prompts para el LLM
    Centralizadas para fácil mantenimiento y A/B testing
    """

    SYSTEM_PROMPT = (
        "Eres un asistente de enseñanza médica experto en oncología pulmonar. "
        "Tu rol es explicar de forma educativa y precisa la progresión del cáncer "
        "de pulmón no microcítico (NSCLC) basándote en:\n\n"
        "1. **Modelo matemático**: Ecuaciones de Gompertz modificadas con dos "
        "poblaciones\n"
        "2. **Evidencia médica**: Guías NCCN, datos SEER, estudios clínicos\n"
        "3. **Contexto del paciente**: Factores de riesgo, tratamientos, y "
        "progresión individual\n\n"
        "**IMPORTANTE:**\n"
        "- Usa SOLO la información proporcionada en el contexto médico\n"
        "- Si no tienes información suficiente, di \"No dispongo de información "
        "específica sobre...\"\n"
        "- Incluye siempre disclaimers educativos\n"
        "- Cita las fuentes cuando des recomendaciones\n\n"
        "**PROHIBIDO:**\n"
        "- Dar diagnósticos definitivos\n"
        "- Recomendar tratamientos como si fuera consulta real\n"
        "- Inventar datos o estadísticas"
    )

    TEACHER_QUERY_TEMPLATE = (
        "**Contexto Médico Recuperado:**\n"
        "{context}\n\n"
        "**Estado del Paciente:**\n"
        "- Edad: {edad} años\n"
        "- Fumador: {es_fumador} (Pack-years: {pack_years})\n"
        "- Dieta: {dieta}\n"
        "- Volumen tumor total: {volumen_total:.2f} cm³ (Sensible: "
        "{volumen_sensible:.2f}, Resistente: {volumen_resistente:.2f})\n"
        "- Estadio aproximado: {estadio}\n"
        "- Tratamiento activo: {tratamiento}\n"
        "- Días de tratamiento: {dias_tratamiento}\n\n"
        "**Pregunta Educativa:**\n"
        "Explica de forma clara y educativa:\n"
        "1. ¿Qué está sucediendo con el tumor en este momento?\n"
        "2. ¿Qué factores del paciente están influyendo "
        "en la progresión?\n"
        "3. ¿Qué opciones terapéuticas se considerarían "
        "según guías NCCN para este estadio?\n"
        "4. ¿Qué debería aprender el estudiante de este caso?\n\n"
        "**Responde en formato:**\n"
        "- **Explicación:** (mecanismo biológico y matemático)\n"
        "- **Recomendación:** (opciones según guías, con disclaimer)\n"
        "- **Fuentes:** (cita específicamente las referencias usadas)"
    )

    PROGRESSION_ANALYSIS_TEMPLATE = (
        "**Contexto Médico:**\n"
        "{context}\n\n"
        "**Análisis de Progresión:**\n"
        "El tumor ha evolucionado desde un volumen inicial de {volumen_inicial:.2f} "
        "cm³ a {volumen_actual:.2f} cm³ en {dias_simulacion} días.\n\n"
        "Tasa de crecimiento observada: {tasa_crecimiento:.3f} cm³/día\n\n"
        "**Pregunta:**\n"
        "Desde una perspectiva educativa, explica:\n"
        "1. ¿Es esta tasa de crecimiento consistente con NSCLC típico?\n"
        "2. ¿Qué factores del paciente podrían estar acelerando o "
        "ralentizando la progresión?\n"
        "3. ¿En qué punto se debería intervenir terapéuticamente según guías NCCN?\n\n"
        "**Incluye referencias específicas a estudios o estadísticas SEER "
        "si están en el contexto.**"
    )

    TREATMENT_RESPONSE_TEMPLATE = (
        "**Contexto Médico:**\n"
        "{context}\n\n"
        "**Tratamiento Aplicado:**\n"
        "- Tipo: {tratamiento}\n"
        "- Duración: {dias_tratamiento} días\n"
        "- Reducción volumen: {reduccion_porcentaje:.1f}%\n"
        "- Población resistente: {volumen_resistente:.2f} cm³\n"
        "  ({porcentaje_resistente:.1f}% del total)\n\n"
        "**Pregunta Educativa:**\n"
        "Analiza la respuesta al tratamiento:\n"
        "1. ¿Es esta reducción consistente con la eficacia esperada "
        "de {tratamiento} según ensayos clínicos?\n"
        "2. ¿La aparición de población resistente es normal?\n"
        "   ¿Cuándo ocurre típicamente?\n"
        "3. ¿Qué estrategias se usan para manejar resistencia según NCCN "
        "Guidelines?\n"
        "4. ¿Qué debería monitorear un clínico en casos similares?\n\n"
        "**Usa datos específicos del contexto para fundamentar tu respuesta.**"
    )

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
            return (
                "No se encontró información médica específica en la base "
                "de conocimiento."
            )

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

        # Support both Spanish and English key names for robustness
        edad = state.get("edad") if state.get("edad") is not None else state.get("age")
        es_fumador = state.get("es_fumador") if state.get("es_fumador") is not None else state.get("is_smoker", False)
        pack_years = state.get("pack_years") if state.get("pack_years") is not None else state.get("pack_years", 0)
        dieta = state.get("dieta") if state.get("dieta") is not None else state.get("diet", "normal")
        vol_sensible = state.get("volumen_tumor_sensible") if state.get("volumen_tumor_sensible") is not None else state.get("sensitive_tumor_volume", 0.0)
        vol_resistente = state.get("volumen_tumor_resistente") if state.get("volumen_tumor_resistente") is not None else state.get("resistant_tumor_volume", 0.0)
        estadio = state.get("estadio_aproximado") or state.get("approx_stage") or "No calculado"
        tratamiento = state.get("tratamiento_activo") if state.get("tratamiento_activo") is not None else state.get("active_treatment", "ninguno")
        dias_tratamiento = state.get("dias_tratamiento") if state.get("dias_tratamiento") is not None else state.get("treatment_days", 0)

        return PromptTemplates.TEACHER_QUERY_TEMPLATE.format(
            context=context,
            edad=edad,
            es_fumador="Sí" if es_fumador else "No",
            pack_years=pack_years,
            dieta=dieta,
            volumen_total=vol_sensible + vol_resistente,
            volumen_sensible=vol_sensible,
            volumen_resistente=vol_resistente,
            estadio=estadio,
            tratamiento=tratamiento,
            dias_tratamiento=dias_tratamiento,
        )
