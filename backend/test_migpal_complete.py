#!/usr/bin/env python3
"""
MigPal Complete Testing Script
Simula todas las interacciones del usuario y verifica que funcionen correctamente.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from typing import Dict, Any, List, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos de MigPal
try:
    from app.services.telegram_bot import get_user_data, save_user_data, get_state, set_state, STATE_NAME, STATE_START
    from app.services.case_storage import delete_user_data
    from app.services.intent_detector import detect_intent, Intent
    from app.services.knowledge_base.cities_top_1000 import search_cities
    from app.services.city_comparator import compare_cities, format_city_full
    from app.services.education_search import search_schools, search_universities
    from app.services.visual_generator import generate_comparison_chart, generate_radar_chart, MATPLOTLIB_AVAILABLE
    from app.services.pdf_report_generator import generate_diagnostic_pdf, generate_city_pdf, REPORTLAB_AVAILABLE
    from app.services.housing_scraper import HousingScraper
    logger.info("✅ Todos los módulos importados correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando módulos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test user ID
TEST_USER_ID = 999999999

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

class MigPalTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.user_id = TEST_USER_ID
    
    def add_result(self, name: str, passed: bool, message: str = ""):
        self.results.append(TestResult(name, passed, message))
        status = "✅" if passed else "❌"
        logger.info(f"{status} {name}: {message}")
    
    def cleanup(self):
        """Limpia datos de prueba"""
        try:
            delete_user_data(self.user_id)
            self.add_result("Cleanup", True, "Datos de prueba eliminados")
        except Exception as e:
            self.add_result("Cleanup", False, str(e))
    
    # ============== TESTS DE MÓDULOS ==============
    
    def test_intent_detection(self):
        """Test del detector de intenciones"""
        # Algunos intents pueden tener variaciones válidas
        test_cases = [
            ("Hola", [Intent.GREETING]),
            ("Quiero ver ciudades en Florida", [Intent.EXPLORE_CITIES, Intent.EXPLORE_STATE]),  # Ambos son válidos
            ("Busco casa en Miami", [Intent.SEARCH_HOUSING]),
            ("Compara Austin con Dallas", [Intent.COMPARE_CITIES]),
            ("Escuelas para mis hijos", [Intent.SEARCH_SCHOOLS]),
            ("Busco trabajo en tecnología", [Intent.SEARCH_JOBS]),
            ("Gracias", [Intent.THANKS]),
            ("Ayuda", [Intent.HELP]),
        ]
        
        passed = 0
        failed = 0
        
        for text, valid_intents in test_cases:
            result = detect_intent(text)
            if result.intent in valid_intents:
                passed += 1
            else:
                failed += 1
                logger.warning(f"  Intent mismatch: '{text}' -> {result.intent} (expected one of {valid_intents})")
        
        self.add_result(
            "Intent Detection",
            failed == 0,
            f"{passed}/{len(test_cases)} intenciones detectadas correctamente"
        )
    
    def test_city_search(self):
        """Test de búsqueda de ciudades"""
        try:
            # Buscar por nombre
            results = search_cities("Miami")
            if not results:
                self.add_result("City Search - Miami", False, "No se encontró Miami")
                return
            
            miami = results[0]
            assert miami.get("name") == "Miami", "Nombre incorrecto"
            assert miami.get("state") in ["FL", "Florida"], f"Estado incorrecto: {miami.get('state')}"
            assert "scores" in miami, "Falta scores"
            
            # Buscar por estado
            results_fl = search_cities("Florida", limit=5)
            assert len(results_fl) > 0, "No se encontraron ciudades en Florida"
            
            # Buscar por estado abreviado
            results_tx = search_cities("TX", limit=5)
            assert len(results_tx) > 0, "No se encontraron ciudades en TX"
            
            self.add_result("City Search", True, f"Miami encontrado, FL: {len(results_fl)} ciudades, TX: {len(results_tx)} ciudades")
        except Exception as e:
            self.add_result("City Search", False, str(e))
    
    def test_city_comparison(self):
        """Test de comparación de ciudades"""
        try:
            miami_results = search_cities("Miami")
            orlando_results = search_cities("Orlando")
            
            if not miami_results or not orlando_results:
                self.add_result("City Comparison", False, "No se encontraron ciudades")
                return
            
            result = compare_cities(miami_results[0], orlando_results[0])
            
            assert result.city1 is not None, "city1 es None"
            assert result.city2 is not None, "city2 es None"
            assert result.winner_overall, "No hay ganador"
            assert result.formatted_message, "No hay mensaje formateado"
            
            self.add_result("City Comparison", True, f"Ganador: {result.winner_overall}")
        except Exception as e:
            self.add_result("City Comparison", False, str(e))
    
    def test_school_search(self):
        """Test de búsqueda de escuelas"""
        try:
            from app.services.education_search import SchoolType
            schools = search_schools("Miami", "FL", school_type=SchoolType.ELEMENTARY)
            assert len(schools) > 0, "No se encontraron escuelas"
            
            school = schools[0]
            assert hasattr(school, 'name'), "Falta nombre"
            assert hasattr(school, 'type'), "Falta tipo"
            
            self.add_result("School Search", True, f"{len(schools)} escuelas encontradas en Miami")
        except Exception as e:
            self.add_result("School Search", False, str(e))
    
    def test_university_search(self):
        """Test de búsqueda de universidades"""
        try:
            # Probar con nombre completo (ahora con mapeo)
            universities = search_universities("Florida")
            if len(universities) == 0:
                # Probar con abreviatura
                universities = search_universities("FL")
            
            assert len(universities) > 0, "No se encontraron universidades en Florida/FL"
            
            uni = universities[0]
            assert hasattr(uni, 'name'), "Falta nombre"
            
            self.add_result("University Search", True, f"{len(universities)} universidades encontradas")
        except Exception as e:
            self.add_result("University Search", False, str(e))
    
    def test_chart_generation(self):
        """Test de generación de gráficos"""
        if not MATPLOTLIB_AVAILABLE:
            self.add_result("Chart Generation", False, "matplotlib no disponible")
            return
        
        try:
            # Test comparison chart
            scores1 = {"costo_vida": 70, "seguridad": 80, "oportunidades": 75}
            scores2 = {"costo_vida": 60, "seguridad": 85, "oportunidades": 80}
            
            chart_bytes = generate_comparison_chart("Miami", scores1, "Orlando", scores2)
            assert chart_bytes is not None, "No se generó el gráfico de comparación"
            assert len(chart_bytes) > 1000, "Gráfico muy pequeño"
            
            # Test radar chart
            radar_bytes = generate_radar_chart("Miami", scores1)
            assert radar_bytes is not None, "No se generó el gráfico radar"
            
            self.add_result("Chart Generation", True, f"Comparison: {len(chart_bytes)} bytes, Radar: {len(radar_bytes)} bytes")
        except Exception as e:
            self.add_result("Chart Generation", False, str(e))
    
    def test_pdf_generation(self):
        """Test de generación de PDFs"""
        if not REPORTLAB_AVAILABLE:
            self.add_result("PDF Generation", False, "reportlab no disponible")
            return
        
        try:
            # Test diagnostic PDF
            user_data = {
                "profile": {
                    "personal": {"name": "Test User", "nationality": "Colombiano"},
                    "education": {"level": "Universitario"},
                    "work": {"profession": "Ingeniero"}
                }
            }
            visa_analysis = {"recommended_visa": "H-1B", "probability": 70}
            recommendations = ["Completar perfil", "Reunir documentos"]
            
            pdf_bytes = generate_diagnostic_pdf("Test User", user_data, visa_analysis, recommendations)
            assert pdf_bytes is not None, "No se generó el PDF de diagnóstico"
            assert len(pdf_bytes) > 1000, "PDF muy pequeño"
            
            # Test city PDF
            miami = search_cities("Miami")[0]
            city_pdf = generate_city_pdf(miami)
            assert city_pdf is not None, "No se generó el PDF de ciudad"
            
            self.add_result("PDF Generation", True, f"Diagnostic: {len(pdf_bytes)} bytes, City: {len(city_pdf)} bytes")
        except Exception as e:
            self.add_result("PDF Generation", False, str(e))
    
    def test_user_data_storage(self):
        """Test de almacenamiento de datos de usuario"""
        try:
            # Crear usuario
            user = get_user_data(self.user_id)
            user["profile"]["personal"]["name"] = "Test User"
            user["profile"]["personal"]["nationality"] = "Colombiano"
            save_user_data(self.user_id, user)
            
            # Verificar que se guardó
            loaded = get_user_data(self.user_id)
            assert loaded["profile"]["personal"]["name"] == "Test User", "Nombre no guardado"
            
            # Test estados
            set_state(self.user_id, "test_state")
            state = get_state(self.user_id)
            assert state == "test_state", "Estado no guardado"
            
            self.add_result("User Data Storage", True, "Datos guardados y recuperados correctamente")
        except Exception as e:
            self.add_result("User Data Storage", False, str(e))
    
    def test_flow_callbacks(self):
        """Test de callbacks del flujo de migración"""
        try:
            # Simular datos de usuario
            user = get_user_data(self.user_id)
            
            # Test flow_why_work
            user["profile"]["migration"] = {"reason": "work", "reason_text": "mejores oportunidades laborales"}
            save_user_data(self.user_id, user)
            
            loaded = get_user_data(self.user_id)
            assert loaded["profile"]["migration"]["reason"] == "work", "Razón no guardada"
            
            # Test flow_region_south
            user["profile"]["migration"]["region"] = "south"
            save_user_data(self.user_id, user)
            
            # Test flow_state_florida
            user["selected_route"] = {"state": "Florida"}
            save_user_data(self.user_id, user)
            
            loaded = get_user_data(self.user_id)
            assert loaded["selected_route"]["state"] == "Florida", "Estado no guardado"
            
            # Test flow_select_city
            user["selected_route"]["city"] = "Miami"
            save_user_data(self.user_id, user)
            
            # Test flow_visa
            user["selected_route"]["visa_type"] = "H-1B"
            user["visa_probability"] = 70
            save_user_data(self.user_id, user)
            
            loaded = get_user_data(self.user_id)
            assert loaded["selected_route"]["visa_type"] == "H-1B", "Visa no guardada"
            assert loaded["visa_probability"] == 70, "Probabilidad no guardada"
            
            self.add_result("Flow Callbacks", True, "Todos los datos del flujo guardados correctamente")
        except Exception as e:
            self.add_result("Flow Callbacks", False, str(e))
    
    def test_housing_scraper(self):
        """Test del scraper de viviendas"""
        try:
            scraper = HousingScraper()
            # Solo verificar que la clase se instancia correctamente
            assert scraper is not None, "Scraper no se instanció"
            self.add_result("Housing Scraper", True, "Scraper instanciado correctamente")
        except Exception as e:
            self.add_result("Housing Scraper", False, str(e))
    
    def test_form_states(self):
        """Test de estados de formulario"""
        try:
            # Verificar que los estados existen (ya importados arriba)
            assert STATE_NAME == "name", "STATE_NAME incorrecto"
            assert STATE_START == "start", "STATE_START incorrecto"
            
            # Simular flujo de estados
            set_state(self.user_id, STATE_NAME)
            assert get_state(self.user_id) == STATE_NAME, "Estado NAME no se estableció"
            
            set_state(self.user_id, STATE_START)
            assert get_state(self.user_id) == STATE_START, "Estado START no se estableció"
            
            self.add_result("Form States", True, "Estados de formulario funcionan correctamente")
        except Exception as e:
            self.add_result("Form States", False, str(e))
    
    def test_city_format(self):
        """Test de formateo de información de ciudad"""
        try:
            miami = search_cities("Miami")[0]
            messages = format_city_full(miami)
            
            assert len(messages) > 0, "No se generaron mensajes"
            assert any("Miami" in msg for msg in messages), "Miami no aparece en los mensajes"
            
            self.add_result("City Format", True, f"{len(messages)} mensajes generados para Miami")
        except Exception as e:
            self.add_result("City Format", False, str(e))
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        logger.info("=" * 60)
        logger.info("🧪 INICIANDO TESTING COMPLETO DE MIGPAL")
        logger.info("=" * 60)
        
        # Limpiar antes de empezar
        self.cleanup()
        
        # Ejecutar tests
        self.test_intent_detection()
        self.test_city_search()
        self.test_city_comparison()
        self.test_school_search()
        self.test_university_search()
        self.test_chart_generation()
        self.test_pdf_generation()
        self.test_user_data_storage()
        self.test_flow_callbacks()
        self.test_housing_scraper()
        self.test_form_states()
        self.test_city_format()
        
        # Limpiar después
        self.cleanup()
        
        # Resumen
        logger.info("=" * 60)
        logger.info("📊 RESUMEN DE TESTS")
        logger.info("=" * 60)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} {result.name}")
        
        logger.info("=" * 60)
        logger.info(f"TOTAL: {passed}/{total} tests pasaron ({failed} fallaron)")
        logger.info("=" * 60)
        
        return failed == 0


if __name__ == "__main__":
    tester = MigPalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
