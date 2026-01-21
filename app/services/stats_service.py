"""
Student Stats Service - Performance Tracking & AI Question Generation
Servicio para tracking de estadísticas y generación de preguntas personalizadas
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import (
    ExamAttempt,
    MedicalTopic,
    TopicPerformance,
    User,
)

logger = logging.getLogger(__name__)


class StudentStatsService:
    """
    Servicio de estadísticas de estudiante.
    Implementa un sistema tipo "stats de videojuego" para tracking de desempeño.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # TOPIC PERFORMANCE CRUD
    # =========================================================================

    async def get_or_create_topic_stats(
        self,
        student_id: UUID,
        topic: MedicalTopic
    ) -> TopicPerformance:
        """Obtiene o crea estadísticas para un tema específico"""
        result = await self.db.execute(
            select(TopicPerformance).where(
                TopicPerformance.student_id == student_id,
                TopicPerformance.topic == topic
            )
        )
        stats = result.scalar_one_or_none()

        if not stats:
            stats = TopicPerformance(
                student_id=student_id,
                topic=topic,
                mastery_score=50.0,  # Empezar en nivel medio
            )
            self.db.add(stats)
            await self.db.flush()
            await self.db.refresh(stats)

        return stats

    async def get_all_student_stats(
        self,
        student_id: UUID
    ) -> List[TopicPerformance]:
        """Obtiene todas las estadísticas de un estudiante"""
        result = await self.db.execute(
            select(TopicPerformance)
            .where(TopicPerformance.student_id == student_id)
            .order_by(TopicPerformance.mastery_score.asc())
        )
        return list(result.scalars().all())

    async def get_student_stats_summary(
        self,
        student_id: UUID
    ) -> Dict:
        """
        Resumen de estadísticas del estudiante (para perfil).
        Similar a stats de videojuego.
        """
        stats = await self.get_all_student_stats(student_id)

        if not stats:
            # Inicializar todos los temas
            for topic in MedicalTopic:
                await self.get_or_create_topic_stats(student_id, topic)
            stats = await self.get_all_student_stats(student_id)

        # Calcular métricas globales
        total_questions = sum(s.total_questions for s in stats)
        total_correct = sum(s.correct_answers for s in stats)
        avg_mastery = sum(s.mastery_score for s in stats) / len(stats) if stats else 50

        # Identificar fortalezas y debilidades
        strengths = [s for s in stats if s.mastery_score >= 75]
        weaknesses = [s for s in stats if s.mastery_score < 50]
        needs_review = [s for s in stats if s.needs_review]

        return {
            "overall_score": round(avg_mastery, 1),
            "total_questions_answered": total_questions,
            "total_correct": total_correct,
            "accuracy_rate": round((total_correct / total_questions * 100), 1) if total_questions > 0 else 0,
            "topics_count": len(stats),
            "strengths_count": len(strengths),
            "weaknesses_count": len(weaknesses),
            "needs_review_count": len(needs_review),
            "topics": [
                {
                    "topic": s.topic.value,
                    "mastery_score": round(s.mastery_score, 1),
                    "accuracy_rate": round(s.accuracy_rate, 1),
                    "total_questions": s.total_questions,
                    "current_streak": s.current_streak,
                    "best_streak": s.best_streak,
                    "performance_level": s.performance_level,
                    "is_strength": s.is_strength,
                    "needs_review": s.needs_review,
                    "last_seen": s.last_seen.isoformat() if s.last_seen else None,
                    "trend": s.trend,
                }
                for s in stats
            ]
        }

    # =========================================================================
    # UPDATE STATS AFTER ANSWER
    # =========================================================================

    async def update_stats_after_answer(
        self,
        student_id: UUID,
        topic_str: Optional[str],
        is_correct: bool,
        difficulty: int = 3
    ) -> Optional[TopicPerformance]:
        """
        Actualiza estadísticas después de responder una pregunta.
        Implementa algoritmo de actualización de mastery score.
        """
        if not topic_str:
            return None

        # Convertir string a enum
        try:
            topic = MedicalTopic(topic_str)
        except ValueError:
            logger.warning(f"Topic no reconocido: {topic_str}")
            return None

        stats = await self.get_or_create_topic_stats(student_id, topic)

        # Actualizar contadores
        stats.total_questions += 1
        if is_correct:
            stats.correct_answers += 1
            stats.current_streak += 1
            stats.best_streak = max(stats.best_streak, stats.current_streak)
            stats.last_correct = datetime.utcnow()
        else:
            stats.incorrect_answers += 1
            stats.current_streak = 0
            stats.last_incorrect = datetime.utcnow()

        stats.last_seen = datetime.utcnow()

        # Actualizar mastery score con algoritmo ELO-like
        stats.mastery_score = self._calculate_new_mastery(
            current_score=stats.mastery_score,
            is_correct=is_correct,
            difficulty=difficulty,
            streak=stats.current_streak
        )

        # Actualizar tendencia (promedio móvil de últimas respuestas)
        stats.trend = self._calculate_trend(stats)

        # Marcar como fortaleza o debilidad
        stats.is_strength = stats.mastery_score >= 75
        stats.needs_review = stats.mastery_score < 50 or (
            stats.last_incorrect and
            stats.last_incorrect > (stats.last_correct or datetime.min)
        )

        await self.db.flush()
        return stats

    def _calculate_new_mastery(
        self,
        current_score: float,
        is_correct: bool,
        difficulty: int,
        streak: int
    ) -> float:
        """
        Calcula nuevo mastery score con algoritmo adaptativo.
        Similar a sistemas de rating ELO pero para aprendizaje.
        """
        # K factor base (cuánto cambia por respuesta)
        k_base = 10.0

        # Ajustar K por dificultad (preguntas difíciles valen más)
        k = k_base * (difficulty / 3.0)

        # Bonus por racha
        streak_bonus = min(streak * 0.5, 3.0) if is_correct else 0

        if is_correct:
            # Subir score, pero más difícil subir cuando ya es alto
            potential_gain = (100 - current_score) / 100
            change = k * potential_gain + streak_bonus
            new_score = min(100, current_score + change)
        else:
            # Bajar score, pero proteger un poco los scores bajos
            potential_loss = current_score / 100
            change = k * potential_loss
            new_score = max(0, current_score - change)

        return new_score

    def _calculate_trend(self, stats: TopicPerformance) -> float:
        """Calcula tendencia basada en últimas respuestas"""
        if stats.total_questions < 3:
            return 0.0

        # Tendencia positiva si accuracy reciente > histórica
        if stats.is_strength:
            return 1.0  # Mejorando
        elif stats.needs_review:
            return -1.0  # Empeorando
        else:
            return 0.0  # Estable

    # =========================================================================
    # PERSONALIZED QUESTION SELECTION ALGORITHM
    # =========================================================================

    async def get_personalized_question_targets(
        self,
        student_id: UUID,
        count: int = 4
    ) -> List[Tuple[MedicalTopic, str, int]]:
        """
        Algoritmo de selección de 4 preguntas personalizadas.
        Retorna lista de (topic, reason, target_difficulty).

        Distribución:
        - 1 pregunta: Punto débil crítico (mastery < 40)
        - 1 pregunta: Área intermedia que necesita refuerzo (40-60)
        - 1 pregunta: Punto fuerte no visto recientemente (refresh)
        - 1 pregunta: Desafío en área de comfort (para avanzar)
        """
        stats = await self.get_all_student_stats(student_id)

        # Inicializar si no hay stats
        if len(stats) < len(MedicalTopic):
            for topic in MedicalTopic:
                await self.get_or_create_topic_stats(student_id, topic)
            stats = await self.get_all_student_stats(student_id)

        targets = []
        now = datetime.utcnow()

        # 1. PUNTO DÉBIL CRÍTICO (mastery < 40)
        weaknesses = [
            s for s in stats
            if s.mastery_score < 40 and s.total_questions > 0
        ]
        if weaknesses:
            # Elegir el más débil
            weakest = min(weaknesses, key=lambda s: s.mastery_score)
            targets.append((weakest.topic, "weakness", 2))  # Dificultad baja para reforzar
        else:
            # Si no hay debilidades críticas, buscar área con más errores recientes
            recent_errors = [
                s for s in stats
                if s.last_incorrect and s.last_incorrect > (now - timedelta(days=7))
            ]
            if recent_errors:
                target = max(recent_errors, key=lambda s: s.incorrect_answers)
                targets.append((target.topic, "recent_errors", 2))

        # 2. ÁREA INTERMEDIA (40-60 mastery, necesita refuerzo)
        intermediate = [
            s for s in stats
            if 40 <= s.mastery_score < 60
        ]
        if intermediate:
            # Elegir la más cercana a subir de nivel
            closest_to_improve = max(intermediate, key=lambda s: s.mastery_score)
            targets.append((closest_to_improve.topic, "intermediate", 3))

        # 3. PUNTO FUERTE NO VISTO RECIENTEMENTE (refresh)
        strengths = [
            s for s in stats
            if s.mastery_score >= 70
        ]
        forgotten_strengths = [
            s for s in strengths
            if not s.last_seen or s.last_seen < (now - timedelta(days=14))
        ]
        if forgotten_strengths:
            # Elegir el más olvidado
            most_forgotten = min(forgotten_strengths, key=lambda s: s.last_seen or datetime.min)
            targets.append((most_forgotten.topic, "forgotten_strength", 3))
        elif strengths:
            # Si todos los fuertes están frescos, elegir uno al azar para desafío
            import random
            target = random.choice(strengths)
            targets.append((target.topic, "strength_refresh", 4))

        # 4. DESAFÍO (punto fuerte con dificultad alta)
        if len(targets) < count and strengths:
            best = max(strengths, key=lambda s: s.mastery_score)
            if best.topic not in [t[0] for t in targets]:
                targets.append((best.topic, "challenge", 5))

        # Completar con temas no vistos si faltan
        unseen = [
            s for s in stats
            if s.total_questions == 0
        ]
        while len(targets) < count and unseen:
            target = unseen.pop(0)
            targets.append((target.topic, "new_topic", 3))

        # Si aún faltan, repetir debilidades
        while len(targets) < count:
            all_sorted = sorted(stats, key=lambda s: s.mastery_score)
            for s in all_sorted:
                if s.topic not in [t[0] for t in targets]:
                    targets.append((s.topic, "reinforcement", 3))
                    break
            else:
                break  # No hay más temas disponibles

        return targets[:count]

    # =========================================================================
    # PROFESSOR VIEW: STUDENT STATS
    # =========================================================================

    async def get_class_stats(
        self,
        professor_id: UUID
    ) -> List[Dict]:
        """
        Obtiene estadísticas de todos los estudiantes que han tomado
        exámenes creados por este profesor.
        """
        # Obtener IDs de estudiantes que han intentado exámenes del profesor
        from app.models.db_models import Exam

        result = await self.db.execute(
            select(ExamAttempt.student_id)
            .join(Exam, ExamAttempt.exam_id == Exam.id)
            .where(Exam.creator_id == professor_id)
            .distinct()
        )
        student_ids = [row[0] for row in result.fetchall()]

        class_stats = []
        for student_id in student_ids:
            # Obtener usuario
            user_result = await self.db.execute(
                select(User).where(User.id == student_id)
            )
            student = user_result.scalar_one_or_none()
            if not student:
                continue

            # Obtener stats
            summary = await self.get_student_stats_summary(student_id)

            class_stats.append({
                "student_id": str(student_id),
                "student_name": student.full_name,
                "student_email": student.email,
                "overall_score": summary["overall_score"],
                "total_questions_answered": summary["total_questions_answered"],
                "accuracy_rate": summary["accuracy_rate"],
                "strengths_count": summary["strengths_count"],
                "weaknesses_count": summary["weaknesses_count"],
                "topics": summary["topics"]
            })

        # Ordenar por score general
        class_stats.sort(key=lambda x: x["overall_score"], reverse=True)
        return class_stats


def get_stats_service(db: AsyncSession) -> StudentStatsService:
    """Factory para StudentStatsService (Dependency Injection)"""
    return StudentStatsService(db)
