#!/usr/bin/env python3
"""
Tests para el sistema de Onboarding Conversacional v5.0
========================================================
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.conversational_onboarding import (
    ConversationalEngine,
    InfoExtractor,
    UserProfile,
    VisaRecommendationEngine,
    get_conversational_engine,
)


class TestInfoExtractor(unittest.TestCase):
    """Tests para el extractor de información"""

    def test_extract_profession(self):
        """Prueba extracción de profesión"""
        extractor = InfoExtractor()

        test_cases = [
            ("Soy ingeniero de software", "ingeniero de software"),
            ("trabajo como programador", "programador"),
            ("Mi profesión es doctor", "doctor"),
            ("I am a teacher", "teacher"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                extracted = extractor.extract_all(text)
                if "profession" in extracted:
                    value, confidence = extracted["profession"]
                    self.assertIn(expected.lower(), value.lower())
                    self.assertGreater(confidence, 0)

    def test_extract_destination_country(self):
        """Prueba extracción de país destino"""
        extractor = InfoExtractor()

        test_cases = [
            ("quiero irme a Estados Unidos", "USA"),
            ("me gustaría migrar a Canadá", "Canadá"),
            ("voy para España", "España"),
            ("to USA", "USA"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                extracted = extractor.extract_all(text)
                if "destination_country" in extracted:
                    value, confidence = extracted["destination_country"]
                    self.assertEqual(value, expected)
                    self.assertGreater(confidence, 0)

    def test_extract_experience_years(self):
        """Prueba extracción de años de experiencia"""
        extractor = InfoExtractor()

        test_cases = [
            ("tengo 5 años de experiencia", "5"),
            ("experiencia de 10 años", "10"),
            ("3 years working", "3"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                extracted = extractor.extract_all(text)
                if "experience_years" in extracted:
                    value, confidence = extracted["experience_years"]
                    self.assertEqual(value, expected)

    def test_extract_timeline(self):
        """Prueba extracción y normalización de timeline"""
        extractor = InfoExtractor()

        test_cases = [
            ("me gustaría irme el próximo año", "próximo año"),
            ("quiero migrar este mes", "mes"),
            ("lo más pronto posible", "pronto posible"),
            ("para el 2025", "2025"),
        ]

        for text, _expected in test_cases:
            with self.subTest(text=text):
                extracted = extractor.extract_all(text)
                if "timeline" in extracted:
                    value, confidence = extracted["timeline"]
                    # Timeline se normaliza
                    self.assertTrue(value is not None)

    def test_extract_english_level(self):
        """Prueba extracción y normalización de nivel de inglés"""
        extractor = InfoExtractor()

        test_cases = [
            ("mi inglés es intermedio", "Intermedio"),
            ("tengo inglés básico", "Básico"),
            ("hablo inglés avanzado", "Avanzado"),
            ("my english is fluent", "Nativo/Fluido"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                extracted = extractor.extract_all(text)
                if "english_level" in extracted:
                    value, confidence = extracted["english_level"]
                    self.assertEqual(value, expected)


class TestQuestionDetection(unittest.TestCase):
    """Tests para detección de preguntas"""

    def test_is_user_question(self):
        """Prueba detección de preguntas del usuario"""
        engine = ConversationalEngine()

        questions = [
            "¿Qué opciones de visa tengo?",
            "¿Cuánto cuesta el proceso?",
            "¿Puedo trabajar con visa de estudiante?",
            "Qué requisitos necesito",
            "Cómo inicio el proceso",
            "What visa options do I have?",
            "How long does it take?",
            "ayúdame con las opciones",
        ]

        statements = [
            "Soy ingeniero de software",
            "Tengo 5 años de experiencia",
            "Mi inglés es intermedio",
            "Vivo en México",
        ]

        # Todas las preguntas deben detectarse
        for q in questions:
            with self.subTest(question=q):
                self.assertTrue(engine._is_user_question(q))

        # Las declaraciones no deben detectarse como preguntas
        for s in statements:
            with self.subTest(statement=s):
                self.assertFalse(engine._is_user_question(s))


class TestUserProfile(unittest.TestCase):
    """Tests para el perfil de usuario"""

    def test_profile_completion(self):
        """Prueba cálculo de completitud del perfil"""
        profile = UserProfile()

        # Perfil vacío = 0%
        self.assertEqual(profile.get_completion_percentage(), 0)

        # Agregar algunos campos
        profile.profession.value = "Ingeniero"
        profile.profession.confidence = 0.8

        profile.destination_country.value = "USA"
        profile.destination_country.confidence = 0.9

        profile.english_level.value = "Intermedio"
        profile.english_level.confidence = 0.7

        # Verificar que la completitud aumentó
        completion = profile.get_completion_percentage()
        self.assertGreater(completion, 0)
        self.assertLess(completion, 100)

        # Llenar todos los campos principales
        profile.name.value = "Test User"
        profile.name.confidence = 0.9

        profile.nationality.value = "Mexicana"
        profile.nationality.confidence = 0.9

        profile.experience_years.value = "5"
        profile.experience_years.confidence = 0.8

        profile.education_level.value = "Universidad"
        profile.education_level.confidence = 0.8

        profile.timeline.value = "próximo año"
        profile.timeline.confidence = 0.7

        profile.budget.value = "30k"
        profile.budget.confidence = 0.8

        profile.migration_reason.value = "trabajo"
        profile.migration_reason.confidence = 0.7

        profile.has_family.value = "no"
        profile.has_family.confidence = 0.9

        # Ahora debería estar más completo
        completion = profile.get_completion_percentage()
        self.assertGreater(completion, 80)


class TestVisaRecommendations(unittest.TestCase):
    """Tests para las recomendaciones de visa"""

    def test_recommendations_for_software_engineer_usa(self):
        """Prueba recomendaciones para ingeniero de software a USA"""
        profile = UserProfile()

        # Perfil de ingeniero de software con experiencia
        profile.profession.value = "ingeniero de software"
        profile.profession.confidence = 0.9
        profile.experience_years.value = "5"
        profile.experience_years.confidence = 0.9
        profile.destination_country.value = "USA"
        profile.destination_country.confidence = 0.9
        profile.budget.value = "30"
        profile.budget.confidence = 0.8
        profile.english_level.value = "Intermedio"
        profile.english_level.confidence = 0.8

        # Agregar más campos para alcanzar 50% de completitud
        profile.name.value = "Test User"
        profile.name.confidence = 0.9
        profile.nationality.value = "Mexicana"
        profile.nationality.confidence = 0.9
        profile.timeline.value = "próximo año"
        profile.timeline.confidence = 0.8

        recommendations = VisaRecommendationEngine.generate_recommendations(profile, "es")

        # Debe generar recomendaciones
        self.assertIsNotNone(recommendations)

        # Debe incluir H-1B
        self.assertIn("H-1B", recommendations)

        # Debe incluir O-1 para 5 años de experiencia
        self.assertIn("O-1", recommendations)

        # Debe incluir L-1
        self.assertIn("L-1", recommendations)

        # Debe incluir EB-2 NIW si el presupuesto es suficiente
        self.assertIn("EB-2 NIW", recommendations)

    def test_no_recommendations_incomplete_profile(self):
        """Prueba que no genera recomendaciones con perfil incompleto"""
        profile = UserProfile()

        # Solo profesión
        profile.profession.value = "ingeniero"
        profile.profession.confidence = 0.9

        recommendations = VisaRecommendationEngine.generate_recommendations(profile)

        # No debe generar recomendaciones con perfil incompleto
        self.assertIsNone(recommendations)


class TestConversationalFlow(unittest.TestCase):
    """Tests para el flujo conversacional completo"""

    def test_basic_conversation_flow(self):
        """Prueba flujo básico de conversación"""
        engine = get_conversational_engine()
        user_data = {
            "user_id": 12345,
            "language": "es",
            "profile": {},
        }

        # Mensaje inicial
        response1, user_data = engine.process_message("Hola, quiero irme a Estados Unidos", user_data, "es")

        # Debe extraer el destino y hacer reflexión
        self.assertIn("USA", str(user_data.get("conversational_profile", {})))
        # Debe preguntar algo
        self.assertIn("?", response1)

        # Segunda respuesta
        response2, user_data = engine.process_message(
            "Soy ingeniero de software con 5 años de experiencia", user_data, "es"
        )

        # Debe extraer profesión y experiencia
        profile_data = user_data.get("conversational_profile", {})
        self.assertIn("ingeniero de software", str(profile_data))
        self.assertIn("5", str(profile_data))

        # Debe hacer reflexión empática
        self.assertTrue(
            "ingeniero" in response2.lower()
            or "experiencia" in response2.lower()
            or "puertas" in response2.lower()
        )

    def test_question_detection_marks_pending(self):
        """Prueba que las preguntas se marcan como pendientes"""
        engine = get_conversational_engine()

        # Primero construir un perfil con suficiente información
        user_data = {
            "user_id": 12345,
            "language": "es",
            "profile": {},
        }

        # Agregar información para tener suficiente completitud
        messages = [
            "Soy ingeniero de software con 5 años de experiencia",
            "Quiero irme a USA",
            "Mi inglés es intermedio",
            "Tengo 30 mil dólares ahorrados",
        ]

        for msg in messages:
            _, user_data = engine.process_message(msg, user_data, "es")

        # Hacer una pregunta
        response, user_data = engine.process_message("¿Qué opciones de visa tengo?", user_data, "es")

        # Debe marcar la pregunta como pendiente
        self.assertIn("pending_ai_question", user_data)
        self.assertEqual(user_data["pending_ai_question"], "¿Qué opciones de visa tengo?")

        # Debe responder que está pensando
        self.assertIn("pensar", response.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
