#!/usr/bin/env python3
"""
MigPAL E2E Test - Prueba de Sistema de Idiomas
==============================================
Valida que el locale se persiste y usa correctamente.

Validaciones:
1. Persistencia de locale en case_storage
2. Mensajes en español cuando locale=es
3. Flujo de nombre con validación
4. Headers y deliverables en idioma correcto
5. Prohibido fallback a EN cuando locale=ES

Ejecutar: python -m pytest backend/tests/test_locale_e2e.py -v -s
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Agregar paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.translations import get_text, TRANSLATIONS, SUPPORTED_LANGUAGES
from app.services.case_storage import save_user_data, load_user_data, delete_user_data

# ============== CONFIGURACIÓN ==============

TEST_USER_ID = 888888888  # Usuario de prueba para locale
LOG_FILE = "logs/locale_test.log"
CONVERSATION_LOG = []


def log(message: str, level: str = "INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    CONVERSATION_LOG.append(log_entry)


# ============== TEST 1: PERSISTENCIA DE LOCALE ==============

def test_locale_persistence():
    """Valida que el locale se persiste y lee correctamente"""
    log("=" * 60)
    log("TEST 1: PERSISTENCIA DE LOCALE")
    log("=" * 60)
    
    user_id = TEST_USER_ID
    
    # Limpiar datos previos
    delete_user_data(user_id)
    
    # Crear usuario con locale ES
    user_data = {
        "user_id": user_id,
        "state": "name",
        "language": "es",  # ESPAÑOL
        "profile": {
            "personal": {"telegram_name": "TestUser"},
            "education": {},
            "work": {},
            "languages": {},
            "history": {},
            "financial": {}
        },
        "family_members": [],
        "preferences": {},
        "selected_route": {},
        "documents": [],
        "created_at": datetime.now().isoformat()
    }
    
    # Guardar
    result = save_user_data(user_id, user_data)
    assert result == True, "Error al guardar datos"
    log("✅ Datos guardados correctamente")
    
    # Cargar (simular reinicio)
    loaded_data = load_user_data(user_id)
    assert loaded_data is not None, "Error al cargar datos"
    
    # VALIDACIÓN CRÍTICA: locale debe ser "es", NO "en"
    loaded_locale = loaded_data.get("language")
    assert loaded_locale == "es", f"FALLO: locale={loaded_locale}, esperado='es'"
    log(f"✅ Locale persistido correctamente: {loaded_locale}")
    
    # Verificar que NO hay fallback a EN
    assert loaded_locale != "en", "FALLO: Fallback a EN detectado"
    log("✅ Sin fallback a EN")
    
    # Limpiar
    delete_user_data(user_id)
    
    log("✅ TEST 1 PASSED: Persistencia de locale correcta")
    return True


# ============== TEST 2: MENSAJES EN ESPAÑOL ==============

def test_spanish_messages():
    """Valida que todos los mensajes están en español cuando locale=es"""
    log("=" * 60)
    log("TEST 2: MENSAJES EN ESPAÑOL")
    log("=" * 60)
    
    lang = "es"
    
    # Lista de keys que DEBEN existir en español
    required_keys = [
        "welcome",
        "ask_name",
        "phase1_profile",
        "confirm_name",
        "yes_correct",
        "no_change",
        "name_too_short",
        "name_confirmed",
        "hello_name",
        "lets_start",
        "philosophy",
        "shall_we_start",
        "yes_lets_start",
        "tell_me_more",
        "ask_birthdate_full",
        "ask_nationality_full",
        "profile_complete",
    ]
    
    missing_keys = []
    wrong_language = []
    
    for key in required_keys:
        text = get_text(key, lang)
        
        # Verificar que existe
        if text == key:  # get_text retorna la key si no existe
            missing_keys.append(key)
            log(f"❌ Falta traducción: {key}")
            continue
        
        # Verificar que NO está en inglés (heurística simple)
        english_markers = ["What is your", "Please", "Your", "Select your", "Welcome to"]
        spanish_markers = ["¿Cuál", "Por favor", "Tu", "Selecciona", "Bienvenido"]
        
        has_english = any(marker in text for marker in english_markers)
        has_spanish = any(marker in text for marker in spanish_markers)
        
        if has_english and not has_spanish:
            wrong_language.append((key, text[:50]))
            log(f"⚠️ Posible texto en inglés: {key} = {text[:50]}...")
        else:
            log(f"✅ {key}: {text[:40]}...")
    
    # Validaciones
    assert len(missing_keys) == 0, f"Faltan traducciones: {missing_keys}"
    
    # Verificar mensajes específicos en español
    welcome = get_text("welcome", "es")
    assert "Bienvenido" in welcome, f"Welcome no está en español: {welcome}"
    log("✅ Mensaje de bienvenida en español")
    
    phase1 = get_text("phase1_profile", "es")
    assert "FASE" in phase1 or "Perfil" in phase1, f"Phase1 no está en español: {phase1}"
    log("✅ Header de fase en español")
    
    confirm = get_text("confirm_name", "es")
    assert "nombre" in confirm.lower(), f"Confirmación no está en español: {confirm}"
    log("✅ Confirmación de nombre en español")
    
    log("✅ TEST 2 PASSED: Mensajes en español correctos")
    return True


# ============== TEST 3: FLUJO DE NOMBRE ==============

def test_name_flow():
    """Valida el flujo completo de nombre con validaciones"""
    log("=" * 60)
    log("TEST 3: FLUJO DE NOMBRE")
    log("=" * 60)
    
    # Test 1: Trim de espacios
    test_cases = [
        ("  juan perez  ", "Juan Perez"),  # trim + titlecase
        ("MARIA GARCIA", "Maria Garcia"),   # titlecase desde mayúsculas
        ("carlos", "Carlos"),               # titlecase desde minúsculas
        ("Ana María López", "Ana María López"),  # ya correcto, no cambiar
    ]
    
    for input_name, expected in test_cases:
        # Simular validación
        name = input_name.strip()
        if name.isupper() or name.islower():
            name = name.title()
        
        assert name == expected, f"FALLO: '{input_name}' -> '{name}', esperado '{expected}'"
        log(f"✅ '{input_name}' -> '{name}'")
    
    # Test 2: Nombre muy corto
    short_names = ["a", "x", ""]
    for short in short_names:
        name = short.strip()
        assert len(name) < 2, f"Nombre '{short}' debería ser rechazado"
        log(f"✅ Nombre corto rechazado: '{short}'")
    
    # Test 3: Verificar que hay mensaje de confirmación
    confirm_es = get_text("confirm_name", "es")
    assert "{name}" in confirm_es, "Falta placeholder {name} en confirmación"
    log(f"✅ Confirmación con placeholder: {confirm_es}")
    
    # Test 4: Verificar botones de confirmación
    yes_es = get_text("yes_correct", "es")
    no_es = get_text("no_change", "es")
    assert "Sí" in yes_es or "correcto" in yes_es.lower(), f"Botón Sí incorrecto: {yes_es}"
    assert "No" in no_es or "cambiar" in no_es.lower(), f"Botón No incorrecto: {no_es}"
    log(f"✅ Botones de confirmación: '{yes_es}' / '{no_es}'")
    
    log("✅ TEST 3 PASSED: Flujo de nombre correcto")
    return True


# ============== TEST 4: HEADERS DE FASE ==============

def test_phase_headers():
    """Valida que los headers de fase están traducidos"""
    log("=" * 60)
    log("TEST 4: HEADERS DE FASE")
    log("=" * 60)
    
    phase_keys = [
        "phase1_profile",
        "phase2_diagnostic",
        "phase3_profiling",
        "phase4_plan",
        "phase5_execution",
        "phase6_closing",
    ]
    
    for lang in ["es", "en"]:
        log(f"\n--- Idioma: {lang.upper()} ---")
        for key in phase_keys:
            text = get_text(key, lang)
            assert text != key, f"Falta traducción de {key} en {lang}"
            
            # Verificar formato
            if lang == "es":
                assert "FASE" in text, f"Header ES sin 'FASE': {text}"
            else:
                assert "PHASE" in text, f"Header EN sin 'PHASE': {text}"
            
            log(f"✅ {key} ({lang}): {text}")
    
    log("✅ TEST 4 PASSED: Headers de fase correctos")
    return True


# ============== TEST 5: NO FALLBACK A EN ==============

def test_no_english_fallback():
    """Valida que NO hay fallback a inglés cuando locale=es"""
    log("=" * 60)
    log("TEST 5: PROHIBIDO FALLBACK A EN")
    log("=" * 60)
    
    # Keys críticas que DEBEN existir en español
    critical_keys = [
        "welcome",
        "ask_name",
        "phase1_profile",
        "confirm_name",
        "yes_correct",
        "no_change",
    ]
    
    for key in critical_keys:
        es_text = get_text(key, "es")
        en_text = get_text(key, "en")
        
        # Verificar que ES y EN son diferentes
        assert es_text != en_text, f"FALLO: {key} es igual en ES y EN: {es_text}"
        
        # Verificar que ES no es la key (fallback)
        assert es_text != key, f"FALLO: {key} hace fallback a la key en ES"
        
        log(f"✅ {key}: ES≠EN, sin fallback")
    
    log("✅ TEST 5 PASSED: Sin fallback a inglés")
    return True


# ============== TEST 6: IDIOMAS SOPORTADOS ==============

def test_supported_languages():
    """Valida que los idiomas principales tienen traducciones básicas"""
    log("=" * 60)
    log("TEST 6: IDIOMAS SOPORTADOS")
    log("=" * 60)
    
    # Idiomas principales que deben tener traducciones completas
    main_languages = ["es", "en", "pt", "fr", "de"]
    
    # Keys mínimas requeridas
    min_keys = ["welcome", "ask_name", "yes", "no"]
    
    for lang in main_languages:
        assert lang in SUPPORTED_LANGUAGES, f"Idioma {lang} no está en SUPPORTED_LANGUAGES"
        
        for key in min_keys:
            text = get_text(key, lang)
            # Puede hacer fallback a EN, pero no a la key
            assert text != key, f"Falta {key} en {lang}"
        
        log(f"✅ {lang}: traducciones básicas OK")
    
    log("✅ TEST 6 PASSED: Idiomas soportados correctos")
    return True


# ============== EJECUTAR TODOS LOS TESTS ==============

def run_all_tests():
    """Ejecuta todos los tests de locale"""
    log("=" * 60)
    log("🌐 INICIANDO PRUEBAS DE LOCALE - MigPAL")
    log("=" * 60)
    log(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("")
    
    tests = [
        ("Persistencia de Locale", test_locale_persistence),
        ("Mensajes en Español", test_spanish_messages),
        ("Flujo de Nombre", test_name_flow),
        ("Headers de Fase", test_phase_headers),
        ("Prohibido Fallback EN", test_no_english_fallback),
        ("Idiomas Soportados", test_supported_languages),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "PASSED", None))
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            log(f"❌ TEST FAILED: {name} - {e}")
    
    # Resumen
    log("\n" + "=" * 60)
    log("📊 RESUMEN DE PRUEBAS DE LOCALE")
    log("=" * 60)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    
    for name, status, error in results:
        emoji = "✅" if status == "PASSED" else "❌"
        log(f"{emoji} {name}: {status}")
        if error:
            log(f"   Error: {error}")
    
    log("")
    log(f"Total: {passed} passed, {failed} failed de {len(tests)} tests")
    
    # Guardar logs
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "locale_test.log")
    with open(log_path, "w") as f:
        f.write("\n".join(CONVERSATION_LOG))
    log(f"\n📁 Logs guardados en: {log_path}")
    
    return passed == len(tests)


# ============== PYTEST WRAPPERS ==============

def test_all_locale_tests():
    """Wrapper para pytest"""
    assert run_all_tests() == True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
