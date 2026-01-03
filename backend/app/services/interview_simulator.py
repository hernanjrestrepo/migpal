"""
MigPAL Interview Simulator - Simulador de Entrevista Consular
=============================================================
Práctica de entrevista consular con preguntas frecuentes y feedback AI.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import random
import json


class InterviewType(Enum):
    """Tipos de entrevista"""
    B1B2 = "b1b2"  # Turista/Negocios
    F1 = "f1"  # Estudiante
    H1B = "h1b"  # Trabajo
    L1 = "l1"  # Transferencia
    O1 = "o1"  # Habilidad Extraordinaria
    E2 = "e2"  # Inversionista
    K1 = "k1"  # Prometido/a
    IR1 = "ir1"  # Cónyuge de ciudadano
    IMMIGRANT = "immigrant"  # Inmigrante general


class QuestionCategory(Enum):
    """Categorías de preguntas"""
    PERSONAL = "personal"
    PURPOSE = "purpose"
    TIES = "ties"  # Lazos con país de origen
    FINANCIAL = "financial"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    TRAVEL = "travel"
    FAMILY = "family"
    SPONSOR = "sponsor"
    RELATIONSHIP = "relationship"  # Para visas de prometido/cónyuge


class Difficulty(Enum):
    """Dificultad de la pregunta"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    TRICKY = "tricky"  # Preguntas trampa


@dataclass
class InterviewQuestion:
    """Pregunta de entrevista"""
    id: str
    question_es: str  # Pregunta en español
    question_en: str  # Pregunta en inglés
    category: QuestionCategory
    difficulty: Difficulty
    visa_types: List[str]
    good_answer_tips: List[str]
    bad_answer_examples: List[str]
    follow_up_questions: List[str]
    red_flags: List[str]  # Respuestas que levantan sospechas
    importance: int  # 1-10


# Base de datos de preguntas
INTERVIEW_QUESTIONS: List[InterviewQuestion] = [
    # ============================================================================
    # PREGUNTAS PERSONALES (Todas las visas)
    # ============================================================================
    InterviewQuestion(
        id="personal_1",
        question_es="¿Cuál es su nombre completo?",
        question_en="What is your full name?",
        category=QuestionCategory.PERSONAL,
        difficulty=Difficulty.EASY,
        visa_types=["ALL"],
        good_answer_tips=[
            "Responde exactamente como aparece en tu pasaporte",
            "Habla claro y con confianza",
            "No dudes ni tartamudees"
        ],
        bad_answer_examples=[
            "Dar un nombre diferente al del pasaporte",
            "Dudar sobre tu propio nombre"
        ],
        follow_up_questions=["¿Tiene algún otro nombre o alias?"],
        red_flags=["Inconsistencia con documentos"],
        importance=8
    ),
    
    InterviewQuestion(
        id="personal_2",
        question_es="¿Cuál es su fecha de nacimiento?",
        question_en="What is your date of birth?",
        category=QuestionCategory.PERSONAL,
        difficulty=Difficulty.EASY,
        visa_types=["ALL"],
        good_answer_tips=[
            "Responde en formato mes/día/año (formato USA)",
            "Sé consistente con tus documentos"
        ],
        bad_answer_examples=[
            "Confundir la fecha",
            "Dar formato incorrecto"
        ],
        follow_up_questions=[],
        red_flags=["Fecha diferente a documentos"],
        importance=7
    ),
    
    InterviewQuestion(
        id="personal_3",
        question_es="¿Dónde vive actualmente?",
        question_en="Where do you currently live?",
        category=QuestionCategory.PERSONAL,
        difficulty=Difficulty.EASY,
        visa_types=["ALL"],
        good_answer_tips=[
            "Da tu dirección completa",
            "Menciona cuánto tiempo llevas viviendo ahí",
            "Muestra estabilidad"
        ],
        bad_answer_examples=[
            "Respuestas vagas como 'en la ciudad'",
            "No saber tu propia dirección"
        ],
        follow_up_questions=["¿Cuánto tiempo ha vivido ahí?", "¿Es casa propia o alquilada?"],
        red_flags=["Dirección inconsistente con formularios"],
        importance=6
    ),
    
    # ============================================================================
    # PROPÓSITO DEL VIAJE
    # ============================================================================
    InterviewQuestion(
        id="purpose_1",
        question_es="¿Cuál es el propósito de su viaje a Estados Unidos?",
        question_en="What is the purpose of your trip to the United States?",
        category=QuestionCategory.PURPOSE,
        difficulty=Difficulty.MEDIUM,
        visa_types=["B1B2", "F1", "H1B"],
        good_answer_tips=[
            "Sé específico y conciso",
            "Menciona fechas y lugares si aplica",
            "Muestra que tienes un plan claro",
            "Para turismo: menciona lugares específicos que visitarás"
        ],
        bad_answer_examples=[
            "'Solo quiero conocer' (muy vago)",
            "'Para buscar trabajo' (ilegal con visa de turista)",
            "Respuestas demasiado largas o confusas"
        ],
        follow_up_questions=[
            "¿Por qué eligió esos lugares?",
            "¿Cuánto tiempo planea quedarse?",
            "¿Dónde se hospedará?"
        ],
        red_flags=[
            "Propósito vago o cambiante",
            "Mencionar búsqueda de trabajo con visa de turista",
            "Planes indefinidos"
        ],
        importance=10
    ),
    
    InterviewQuestion(
        id="purpose_2",
        question_es="¿Por qué quiere estudiar en Estados Unidos?",
        question_en="Why do you want to study in the United States?",
        category=QuestionCategory.PURPOSE,
        difficulty=Difficulty.MEDIUM,
        visa_types=["F1"],
        good_answer_tips=[
            "Menciona la calidad del programa específico",
            "Explica cómo beneficiará tu carrera",
            "Muestra que investigaste la universidad",
            "Conecta con tus planes de regreso"
        ],
        bad_answer_examples=[
            "'Porque USA es mejor' (muy genérico)",
            "'Para quedarme después' (intención de inmigrante)",
            "No saber nada sobre el programa"
        ],
        follow_up_questions=[
            "¿Por qué esta universidad específicamente?",
            "¿Qué hará después de graduarse?",
            "¿Por qué no estudiar en su país?"
        ],
        red_flags=[
            "No conocer detalles del programa",
            "Mencionar quedarse permanentemente"
        ],
        importance=10
    ),
    
    # ============================================================================
    # LAZOS CON PAÍS DE ORIGEN
    # ============================================================================
    InterviewQuestion(
        id="ties_1",
        question_es="¿Qué lo motiva a regresar a su país?",
        question_en="What motivates you to return to your country?",
        category=QuestionCategory.TIES,
        difficulty=Difficulty.HARD,
        visa_types=["B1B2", "F1"],
        good_answer_tips=[
            "Menciona familia (especialmente hijos, padres mayores)",
            "Habla de tu trabajo o negocio",
            "Menciona propiedades o inversiones",
            "Muestra compromiso con tu comunidad"
        ],
        bad_answer_examples=[
            "'No tengo nada que me ate' (red flag mayor)",
            "'Mi familia puede venir después'",
            "No poder mencionar lazos concretos"
        ],
        follow_up_questions=[
            "¿Tiene familia en Estados Unidos?",
            "¿Ha pensado en quedarse permanentemente?"
        ],
        red_flags=[
            "Sin lazos familiares fuertes",
            "Sin empleo estable",
            "Sin propiedades"
        ],
        importance=10
    ),
    
    InterviewQuestion(
        id="ties_2",
        question_es="¿Tiene familia en Estados Unidos?",
        question_en="Do you have family in the United States?",
        category=QuestionCategory.TIES,
        difficulty=Difficulty.TRICKY,
        visa_types=["B1B2", "F1"],
        good_answer_tips=[
            "Sé honesto - mentir es peor",
            "Si tienes familia, explica que tu vida está en tu país",
            "Enfatiza tus lazos más fuertes en tu país"
        ],
        bad_answer_examples=[
            "Mentir sobre familia en USA",
            "Decir que planeas quedarte con ellos indefinidamente"
        ],
        follow_up_questions=[
            "¿Qué estatus migratorio tienen?",
            "¿Con qué frecuencia los visita?",
            "¿Planea quedarse con ellos?"
        ],
        red_flags=[
            "Mentir (verificable en sistema)",
            "Familia que ha solicitado petición"
        ],
        importance=9
    ),
    
    # ============================================================================
    # FINANCIERAS
    # ============================================================================
    InterviewQuestion(
        id="financial_1",
        question_es="¿Quién pagará su viaje?",
        question_en="Who will pay for your trip?",
        category=QuestionCategory.FINANCIAL,
        difficulty=Difficulty.MEDIUM,
        visa_types=["B1B2", "F1"],
        good_answer_tips=[
            "Muestra que tienes fondos propios",
            "Si alguien te patrocina, explica la relación",
            "Ten documentos de respaldo listos"
        ],
        bad_answer_examples=[
            "'No sé, alguien me ayudará'",
            "No poder explicar origen de fondos"
        ],
        follow_up_questions=[
            "¿Cuánto dinero tiene ahorrado?",
            "¿Puede mostrar sus estados de cuenta?",
            "¿Cuál es su salario mensual?"
        ],
        red_flags=[
            "Fondos insuficientes",
            "Depósitos recientes grandes sin explicación",
            "Patrocinador sin relación clara"
        ],
        importance=9
    ),
    
    InterviewQuestion(
        id="financial_2",
        question_es="¿Cuál es su salario actual?",
        question_en="What is your current salary?",
        category=QuestionCategory.FINANCIAL,
        difficulty=Difficulty.MEDIUM,
        visa_types=["B1B2", "H1B", "L1"],
        good_answer_tips=[
            "Da cifras exactas",
            "Menciona beneficios adicionales si los hay",
            "Sé consistente con documentos"
        ],
        bad_answer_examples=[
            "No saber tu propio salario",
            "Cifras inconsistentes con documentos"
        ],
        follow_up_questions=[
            "¿Tiene otras fuentes de ingreso?",
            "¿Cuánto tiempo lleva ganando eso?"
        ],
        red_flags=["Salario muy bajo para el viaje planeado"],
        importance=8
    ),
    
    # ============================================================================
    # EMPLEO
    # ============================================================================
    InterviewQuestion(
        id="employment_1",
        question_es="¿En qué trabaja actualmente?",
        question_en="What do you currently do for work?",
        category=QuestionCategory.EMPLOYMENT,
        difficulty=Difficulty.EASY,
        visa_types=["ALL"],
        good_answer_tips=[
            "Describe tu trabajo claramente",
            "Menciona cuánto tiempo llevas",
            "Muestra estabilidad laboral"
        ],
        bad_answer_examples=[
            "'Trabajo en varias cosas' (inestable)",
            "No poder describir tu trabajo"
        ],
        follow_up_questions=[
            "¿Cuánto tiempo lleva en ese trabajo?",
            "¿Le dieron permiso para viajar?",
            "¿Qué pasará con su trabajo mientras viaja?"
        ],
        red_flags=[
            "Desempleado sin explicación",
            "Trabajo informal o inestable"
        ],
        importance=9
    ),
    
    InterviewQuestion(
        id="employment_2",
        question_es="¿Qué hará con su trabajo mientras está en Estados Unidos?",
        question_en="What will happen to your job while you're in the US?",
        category=QuestionCategory.EMPLOYMENT,
        difficulty=Difficulty.MEDIUM,
        visa_types=["B1B2"],
        good_answer_tips=[
            "Muestra que tienes permiso de tu empleador",
            "Explica que tu puesto te espera",
            "Menciona si son vacaciones pagadas"
        ],
        bad_answer_examples=[
            "'Voy a renunciar'",
            "'No sé si tendré trabajo cuando regrese'"
        ],
        follow_up_questions=[
            "¿Tiene carta de su empleador?",
            "¿Cuántos días de vacaciones tiene?"
        ],
        red_flags=["Renunciar para viajar", "Sin garantía de empleo al regresar"],
        importance=8
    ),
    
    # ============================================================================
    # PREGUNTAS PARA H-1B
    # ============================================================================
    InterviewQuestion(
        id="h1b_1",
        question_es="¿Qué hace la empresa que lo está patrocinando?",
        question_en="What does the company sponsoring you do?",
        category=QuestionCategory.SPONSOR,
        difficulty=Difficulty.MEDIUM,
        visa_types=["H1B"],
        good_answer_tips=[
            "Conoce bien a tu empleador",
            "Describe el negocio claramente",
            "Menciona tamaño y ubicación"
        ],
        bad_answer_examples=[
            "No saber qué hace la empresa",
            "Información incorrecta sobre el empleador"
        ],
        follow_up_questions=[
            "¿Cuántos empleados tiene?",
            "¿Dónde está ubicada la oficina?",
            "¿Cuánto tiempo lleva la empresa operando?"
        ],
        red_flags=["No conocer al empleador", "Empresa muy pequeña o nueva"],
        importance=9
    ),
    
    InterviewQuestion(
        id="h1b_2",
        question_es="¿Cuáles serán sus responsabilidades en el trabajo?",
        question_en="What will your job responsibilities be?",
        category=QuestionCategory.EMPLOYMENT,
        difficulty=Difficulty.MEDIUM,
        visa_types=["H1B", "L1", "O1"],
        good_answer_tips=[
            "Describe responsabilidades específicas",
            "Conecta con tu educación y experiencia",
            "Muestra que el puesto requiere tu especialización"
        ],
        bad_answer_examples=[
            "Descripción vaga del trabajo",
            "Responsabilidades que no requieren título"
        ],
        follow_up_questions=[
            "¿Por qué lo eligieron a usted?",
            "¿Qué lo hace calificado para este puesto?"
        ],
        red_flags=["Trabajo que no requiere especialización"],
        importance=9
    ),
    
    # ============================================================================
    # PREGUNTAS PARA O-1
    # ============================================================================
    InterviewQuestion(
        id="o1_1",
        question_es="¿Qué lo hace extraordinario en su campo?",
        question_en="What makes you extraordinary in your field?",
        category=QuestionCategory.EMPLOYMENT,
        difficulty=Difficulty.HARD,
        visa_types=["O1"],
        good_answer_tips=[
            "Menciona premios y reconocimientos específicos",
            "Habla de publicaciones y citas",
            "Describe contribuciones únicas",
            "Sé específico pero no arrogante"
        ],
        bad_answer_examples=[
            "'Soy muy bueno en lo que hago' (muy vago)",
            "No poder mencionar logros específicos"
        ],
        follow_up_questions=[
            "¿Qué premios ha ganado?",
            "¿Cuántas publicaciones tiene?",
            "¿Quién más reconoce su trabajo?"
        ],
        red_flags=["No poder demostrar habilidad extraordinaria"],
        importance=10
    ),
    
    # ============================================================================
    # PREGUNTAS PARA VISA DE PROMETIDO/CÓNYUGE
    # ============================================================================
    InterviewQuestion(
        id="relationship_1",
        question_es="¿Cómo conoció a su pareja?",
        question_en="How did you meet your partner?",
        category=QuestionCategory.RELATIONSHIP,
        difficulty=Difficulty.MEDIUM,
        visa_types=["K1", "IR1"],
        good_answer_tips=[
            "Cuenta la historia con detalles",
            "Sé consistente con lo que dijo tu pareja",
            "Muestra emoción genuina"
        ],
        bad_answer_examples=[
            "Historia vaga o inconsistente",
            "No recordar detalles importantes"
        ],
        follow_up_questions=[
            "¿Cuándo fue la primera vez que se vieron en persona?",
            "¿Cuántas veces se han visto?",
            "¿Cómo se comunican?"
        ],
        red_flags=[
            "Historias inconsistentes entre pareja",
            "Nunca se han visto en persona",
            "Comunicación mínima"
        ],
        importance=10
    ),
    
    InterviewQuestion(
        id="relationship_2",
        question_es="¿Cuándo y dónde se comprometieron?",
        question_en="When and where did you get engaged?",
        category=QuestionCategory.RELATIONSHIP,
        difficulty=Difficulty.MEDIUM,
        visa_types=["K1"],
        good_answer_tips=[
            "Recuerda la fecha exacta",
            "Describe el momento con detalles",
            "Ten fotos del compromiso"
        ],
        bad_answer_examples=[
            "No recordar cuándo fue",
            "Detalles vagos"
        ],
        follow_up_questions=[
            "¿Puede mostrar fotos?",
            "¿Quién más estaba presente?",
            "¿Cómo fue la propuesta?"
        ],
        red_flags=["No recordar detalles del compromiso"],
        importance=9
    ),
    
    # ============================================================================
    # PREGUNTAS TRAMPA
    # ============================================================================
    InterviewQuestion(
        id="tricky_1",
        question_es="¿Ha pensado en quedarse permanentemente en Estados Unidos?",
        question_en="Have you thought about staying permanently in the US?",
        category=QuestionCategory.PURPOSE,
        difficulty=Difficulty.TRICKY,
        visa_types=["B1B2", "F1"],
        good_answer_tips=[
            "Responde honestamente pero enfatiza tu intención de regresar",
            "Menciona tus lazos fuertes con tu país",
            "No digas 'nunca' - suena falso"
        ],
        bad_answer_examples=[
            "'Sí, me encantaría quedarme'",
            "'Nunca, odio Estados Unidos' (extremo)"
        ],
        follow_up_questions=[
            "¿Qué haría si le ofrecen trabajo allá?",
            "¿Tiene planes de inmigrar en el futuro?"
        ],
        red_flags=["Admitir intención de quedarse con visa de no inmigrante"],
        importance=10
    ),
    
    InterviewQuestion(
        id="tricky_2",
        question_es="¿Por qué debería creerle que va a regresar?",
        question_en="Why should I believe you will return?",
        category=QuestionCategory.TIES,
        difficulty=Difficulty.TRICKY,
        visa_types=["B1B2", "F1"],
        good_answer_tips=[
            "Menciona lazos concretos y verificables",
            "Habla de tu carrera y planes futuros en tu país",
            "Muestra documentos de respaldo",
            "Mantén la calma - es una pregunta estándar"
        ],
        bad_answer_examples=[
            "Ponerse nervioso o a la defensiva",
            "'Porque se lo estoy diciendo'",
            "No poder dar razones concretas"
        ],
        follow_up_questions=[],
        red_flags=["No poder dar razones convincentes"],
        importance=10
    ),
]


@dataclass
class SimulationSession:
    """Sesión de simulación de entrevista"""
    id: str
    user_id: int
    interview_type: InterviewType
    questions_asked: List[str] = field(default_factory=list)
    answers: Dict[str, str] = field(default_factory=dict)
    scores: Dict[str, int] = field(default_factory=dict)  # question_id -> score (1-10)
    feedback: Dict[str, str] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    overall_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interview_type": self.interview_type.value,
            "questions_asked": self.questions_asked,
            "answers": self.answers,
            "scores": self.scores,
            "feedback": self.feedback,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "overall_score": self.overall_score
        }


class InterviewSimulator:
    """Simulador de entrevista consular"""
    
    def __init__(self, user_id: int, interview_type: InterviewType, profile_data: Dict = None):
        self.user_id = user_id
        self.interview_type = interview_type
        self.profile_data = profile_data or {}
        self.session: Optional[SimulationSession] = None
        self.current_question_index = 0
        self.questions_pool: List[InterviewQuestion] = []
        self._prepare_questions()
    
    def _prepare_questions(self):
        """Preparar pool de preguntas para el tipo de entrevista"""
        self.questions_pool = []
        
        for q in INTERVIEW_QUESTIONS:
            if "ALL" in q.visa_types or self.interview_type.value.upper() in [v.upper() for v in q.visa_types]:
                self.questions_pool.append(q)
        
        # Ordenar por importancia y mezclar un poco
        self.questions_pool.sort(key=lambda x: (-x.importance, random.random()))
    
    def start_session(self) -> SimulationSession:
        """Iniciar nueva sesión de simulación"""
        session_id = f"{self.user_id}_{self.interview_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.session = SimulationSession(
            id=session_id,
            user_id=self.user_id,
            interview_type=self.interview_type
        )
        
        self.current_question_index = 0
        
        return self.session
    
    def get_next_question(self) -> Optional[InterviewQuestion]:
        """Obtener siguiente pregunta"""
        if self.current_question_index >= len(self.questions_pool):
            return None
        
        question = self.questions_pool[self.current_question_index]
        
        if self.session:
            self.session.questions_asked.append(question.id)
        
        return question
    
    def submit_answer(self, question_id: str, answer: str) -> Dict[str, Any]:
        """Enviar respuesta y obtener feedback"""
        question = None
        for q in self.questions_pool:
            if q.id == question_id:
                question = q
                break
        
        if not question:
            return {"error": "Pregunta no encontrada"}
        
        # Guardar respuesta
        if self.session:
            self.session.answers[question_id] = answer
        
        # Evaluar respuesta (simplificado - en producción usar AI)
        score, feedback = self._evaluate_answer(question, answer)
        
        if self.session:
            self.session.scores[question_id] = score
            self.session.feedback[question_id] = feedback
        
        self.current_question_index += 1
        
        return {
            "score": score,
            "feedback": feedback,
            "tips": question.good_answer_tips,
            "red_flags_to_avoid": question.red_flags,
            "follow_up_possible": question.follow_up_questions
        }
    
    def _evaluate_answer(self, question: InterviewQuestion, answer: str) -> Tuple[int, str]:
        """Evaluar una respuesta (simplificado)"""
        score = 5  # Base score
        feedback_parts = []
        
        answer_lower = answer.lower()
        answer_length = len(answer)
        
        # Evaluar longitud
        if answer_length < 20:
            score -= 2
            feedback_parts.append("Tu respuesta es muy corta. Elabora más.")
        elif answer_length > 500:
            score -= 1
            feedback_parts.append("Tu respuesta es muy larga. Sé más conciso.")
        else:
            score += 1
            feedback_parts.append("Buena longitud de respuesta.")
        
        # Verificar red flags
        for red_flag in question.red_flags:
            if any(word in answer_lower for word in red_flag.lower().split()):
                score -= 2
                feedback_parts.append(f"⚠️ Cuidado: '{red_flag}' puede levantar sospechas.")
        
        # Verificar palabras positivas
        positive_words = ["trabajo", "familia", "regreso", "plan", "empresa", "estudio"]
        for word in positive_words:
            if word in answer_lower:
                score += 0.5
        
        # Verificar confianza
        uncertain_words = ["no sé", "tal vez", "quizás", "creo que", "supongo"]
        for word in uncertain_words:
            if word in answer_lower:
                score -= 1
                feedback_parts.append("Evita mostrar incertidumbre. Sé más seguro en tus respuestas.")
                break
        
        # Ajustar score
        score = max(1, min(10, int(score)))
        
        # Generar feedback final
        if score >= 8:
            feedback_parts.insert(0, "✅ Excelente respuesta!")
        elif score >= 6:
            feedback_parts.insert(0, "👍 Buena respuesta, pero puede mejorar.")
        elif score >= 4:
            feedback_parts.insert(0, "⚠️ Respuesta aceptable, necesita trabajo.")
        else:
            feedback_parts.insert(0, "❌ Esta respuesta podría causar problemas. Practica más.")
        
        return score, " ".join(feedback_parts)
    
    def end_session(self) -> Dict[str, Any]:
        """Finalizar sesión y obtener resumen"""
        if not self.session:
            return {"error": "No hay sesión activa"}
        
        self.session.completed_at = datetime.now()
        
        # Calcular score general
        if self.session.scores:
            self.session.overall_score = sum(self.session.scores.values()) / len(self.session.scores)
        
        # Generar resumen
        summary = self._generate_summary()
        
        return {
            "session": self.session.to_dict(),
            "summary": summary
        }
    
    def _generate_summary(self) -> str:
        """Generar resumen de la sesión"""
        if not self.session:
            return "No hay sesión"
        
        total_questions = len(self.session.questions_asked)
        avg_score = self.session.overall_score
        
        # Identificar áreas de mejora
        weak_areas = []
        strong_areas = []
        
        for q_id, score in self.session.scores.items():
            question = next((q for q in INTERVIEW_QUESTIONS if q.id == q_id), None)
            if question:
                if score < 5:
                    weak_areas.append(question.category.value)
                elif score >= 8:
                    strong_areas.append(question.category.value)
        
        # Barra de progreso
        bar_width = 10
        filled = int(bar_width * avg_score / 10)
        bar = "▓" * filled + "░" * (bar_width - filled)
        
        msg = f"""
📊 **RESUMEN DE TU PRÁCTICA DE ENTREVISTA**

🎯 **Puntuación General:** [{bar}] {avg_score:.1f}/10
📝 **Preguntas respondidas:** {total_questions}

"""
        
        if avg_score >= 8:
            msg += "🌟 **¡Excelente!** Estás muy bien preparado para tu entrevista.\n\n"
        elif avg_score >= 6:
            msg += "👍 **Bien!** Tienes buena preparación pero hay áreas para mejorar.\n\n"
        elif avg_score >= 4:
            msg += "⚠️ **Necesitas más práctica.** Revisa las áreas débiles.\n\n"
        else:
            msg += "❌ **Requiere trabajo significativo.** Practica más antes de tu entrevista.\n\n"
        
        if strong_areas:
            msg += "💪 **Áreas fuertes:**\n"
            for area in set(strong_areas):
                msg += f"   • {area.title()}\n"
            msg += "\n"
        
        if weak_areas:
            msg += "📚 **Áreas a mejorar:**\n"
            for area in set(weak_areas):
                msg += f"   • {area.title()}\n"
            msg += "\n"
        
        msg += """
💡 **Consejos generales:**
• Practica frente a un espejo
• Responde en inglés si puedes
• Mantén contacto visual
• Sé honesto siempre
• Lleva documentos organizados
• Llega temprano a tu cita
"""
        
        return msg
    
    def get_question_by_category(self, category: QuestionCategory) -> Optional[InterviewQuestion]:
        """Obtener pregunta de una categoría específica"""
        category_questions = [q for q in self.questions_pool if q.category == category]
        if category_questions:
            return random.choice(category_questions)
        return None
    
    def format_question_for_telegram(self, question: InterviewQuestion, show_english: bool = True) -> str:
        """Formatear pregunta para Telegram"""
        difficulty_emoji = {
            Difficulty.EASY: "🟢",
            Difficulty.MEDIUM: "🟡",
            Difficulty.HARD: "🔴",
            Difficulty.TRICKY: "⚠️"
        }
        
        msg = f"""
{difficulty_emoji.get(question.difficulty, "🔵")} **Pregunta de Entrevista**

🇪🇸 _{question.question_es}_
"""
        
        if show_english:
            msg += f"\n🇺🇸 _{question.question_en}_\n"
        
        msg += f"""
📁 Categoría: {question.category.value.title()}
⭐ Importancia: {"⭐" * min(question.importance // 2, 5)}

Escribe tu respuesta como si estuvieras en la entrevista real.
"""
        
        return msg


def create_interview_simulator(user_id: int, interview_type: InterviewType, profile_data: Dict = None) -> InterviewSimulator:
    """Factory function"""
    return InterviewSimulator(user_id, interview_type, profile_data)


def get_interview_tips(interview_type: InterviewType) -> str:
    """Obtener tips generales para un tipo de entrevista"""
    tips = {
        InterviewType.B1B2: """
🎯 **TIPS PARA ENTREVISTA B1/B2 (TURISTA)**

✅ **Qué hacer:**
• Lleva todos tus documentos organizados
• Viste profesionalmente
• Responde de forma breve y directa
• Muestra lazos fuertes con tu país
• Ten claro tu itinerario

❌ **Qué NO hacer:**
• No menciones buscar trabajo
• No digas que quieres quedarte
• No lleves documentos falsos
• No mientas sobre familia en USA
• No te pongas nervioso

📋 **Documentos recomendados:**
• Carta de trabajo
• Estados de cuenta
• Títulos de propiedad
• Itinerario de viaje
• Reservas de hotel
""",
        InterviewType.F1: """
🎯 **TIPS PARA ENTREVISTA F-1 (ESTUDIANTE)**

✅ **Qué hacer:**
• Conoce tu programa de estudios
• Explica por qué esa universidad
• Muestra fondos suficientes
• Ten plan claro post-graduación
• Demuestra intención de regresar

❌ **Qué NO hacer:**
• No digas que quieres trabajar en USA
• No menciones quedarte permanentemente
• No desconozcas tu programa
• No tengas fondos insuficientes

📋 **Documentos recomendados:**
• I-20
• Recibo SEVIS
• Carta de aceptación
• Estados de cuenta
• Transcripciones académicas
""",
        InterviewType.H1B: """
🎯 **TIPS PARA ENTREVISTA H-1B (TRABAJO)**

✅ **Qué hacer:**
• Conoce bien a tu empleador
• Entiende tus responsabilidades
• Explica tu especialización
• Ten documentos de educación

❌ **Qué NO hacer:**
• No desconozcas tu empleador
• No tengas descripción vaga del trabajo
• No falten documentos de educación

📋 **Documentos recomendados:**
• Approval Notice (I-797)
• Carta del empleador
• Títulos y transcripciones
• CV actualizado
• Evaluación de credenciales
""",
    }
    
    return tips.get(interview_type, "Tips no disponibles para este tipo de entrevista.")


def get_all_interview_types() -> List[InterviewType]:
    """Obtener todos los tipos de entrevista disponibles"""
    return list(InterviewType)


__all__ = [
    'InterviewType',
    'QuestionCategory',
    'Difficulty',
    'InterviewQuestion',
    'SimulationSession',
    'InterviewSimulator',
    'INTERVIEW_QUESTIONS',
    'create_interview_simulator',
    'get_interview_tips',
    'get_all_interview_types',
]
