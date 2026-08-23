#!/usr/bin/env python3
"""
SEGMENTO 4/4: RELEASE GATE + EVIDENCIA
=======================================
Gate completo que bloquea release si falla cualquier test.

CRITERIOS DE RELEASE:
- 0 crashes
- 0 silent (100% tasa de respuesta)
- 20/20 planes completos en simulación tipo humano
- Prueba manual en Telegram completando Plan Maestro

GENERA:
- Reporte markdown con métricas
- Tasa de respuesta
- Tiempo medio de respuesta
- Fricciones top
- Bugs encontrados/cerrados
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports del proyecto
from app.services.availability_watchdog import get_empathic_fallback
from app.services.flow_governor import InputType, interpret_user_input

# ============== CONFIGURACIÓN ==============

REPORT_DIR = Path(__file__).parent.parent / "reports"
REPORT_FILE = REPORT_DIR / f"release_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

# Criterios de release
REQUIRED_RESPONSE_RATE = 100.0  # 100% obligatorio
MAX_CRASHES = 0
MAX_SILENT = 0
REQUIRED_COMPLETE_PLANS = 20


# ============== DATA CLASSES ==============


@dataclass
class TestMetrics:
    """Métricas de un test"""

    name: str
    passed: bool
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Resultado de una simulación"""

    flow_id: int
    flow_name: str
    completed: bool
    steps_total: int
    steps_completed: int
    response_times: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    friction_points: list[str] = field(default_factory=list)


@dataclass
class ReleaseReport:
    """Reporte completo de release"""

    timestamp: datetime
    version: str

    # Métricas principales
    response_rate: float
    avg_response_time_ms: float
    total_inputs: int
    total_responses: int

    # Crashes y silences
    crashes: int
    silent_failures: int

    # Planes completos
    plans_completed: int
    plans_total: int

    # Tests
    tests_passed: int
    tests_total: int
    test_results: list[TestMetrics] = field(default_factory=list)

    # Simulaciones
    simulations: list[SimulationResult] = field(default_factory=list)

    # Fricciones y bugs
    top_frictions: list[tuple[str, int]] = field(default_factory=list)
    bugs_found: list[str] = field(default_factory=list)
    bugs_closed: list[str] = field(default_factory=list)

    # Verificación manual
    manual_test_completed: bool = False
    manual_test_notes: str = ""

    # Resultado final
    can_release: bool = False
    blocking_reasons: list[str] = field(default_factory=list)


# ============== 20 PLANES COMPLETOS TIPO HUMANO ==============

HUMAN_SIMULATION_PLANS = [
    # Plan 1: Profesional tech soltero
    {
        "name": "Tech Professional Single",
        "persona": "Ingeniero de software, 28 años, Colombia, soltero",
        "steps": [
            "hola, quiero información sobre migrar",
            "me llamo Carlos Rodríguez",
            "soy de Colombia, de Bogotá",
            "tengo 28 años",
            "soy ingeniero de software",
            "trabajo en una startup, llevo 5 años",
            "gano como $4000 al mes",
            "soy soltero, viajo solo",
            "tengo $25,000 ahorrados",
            "quiero irme en los próximos 6 meses",
            "me interesa trabajar en tech",
            "¿qué visa me recomiendas?",
            "ok, suena bien",
            "¿qué ciudades me convienen?",
            "me interesa Austin",
            "¿cuánto cuesta vivir ahí?",
            "perfecto, ¿cuáles son los siguientes pasos?",
        ],
    },
    # Plan 2: Familia con niños
    {
        "name": "Family with Children",
        "persona": "Médico, 38 años, Venezuela, casado con 2 hijos",
        "steps": [
            "buenas tardes",
            "quiero migrar con mi familia",
            "somos 4: mi esposa, mis 2 hijos y yo",
            "me llamo Roberto Méndez",
            "soy de Venezuela",
            "tengo 38 años",
            "soy médico, especialista en pediatría",
            "mi esposa es enfermera",
            "mis hijos tienen 8 y 12 años",
            "tenemos $60,000 ahorrados",
            "queremos irnos lo antes posible",
            "la situación en Venezuela está muy difícil",
            "¿qué opciones tenemos?",
            "¿puedo ejercer como médico allá?",
            "¿qué ciudades tienen buenas escuelas?",
        ],
    },
    # Plan 3: Estudiante
    {
        "name": "Student",
        "persona": "Estudiante, 22 años, México, quiere maestría",
        "steps": [
            "hola!",
            "quiero estudiar en Estados Unidos",
            "me llamo Ana García",
            "soy mexicana, de Guadalajara",
            "tengo 22 años",
            "acabo de terminar mi carrera en administración",
            "quiero hacer una maestría en finanzas",
            "mis papás me van a apoyar económicamente",
            "tenemos como $80,000 para mis estudios",
            "¿qué universidades me recomiendas?",
            "¿cómo es el proceso de visa de estudiante?",
            "¿puedo trabajar mientras estudio?",
        ],
    },
    # Plan 4: Emprendedor
    {
        "name": "Entrepreneur",
        "persona": "Emprendedor, 35 años, Argentina, tiene startup",
        "steps": [
            "hola, necesito asesoría",
            "tengo una startup de tecnología",
            "me llamo Martín López",
            "soy argentino",
            "tengo 35 años",
            "mi empresa factura $500,000 al año",
            "tenemos 10 empleados",
            "quiero expandir a Estados Unidos",
            "viajo con mi esposa",
            "ella también trabaja en la empresa",
            "tenemos $200,000 para invertir",
            "¿qué visa necesito para abrir una empresa?",
            "¿cuál es el mejor estado para incorporar?",
        ],
    },
    # Plan 5: Jubilado
    {
        "name": "Retiree",
        "persona": "Jubilado, 65 años, España, quiere retirarse en Florida",
        "steps": [
            "buenas",
            "quiero retirarme en Estados Unidos",
            "me llamo José Antonio Fernández",
            "soy español",
            "tengo 65 años, ya estoy jubilado",
            "mi esposa tiene 62",
            "recibo una pensión de €2,500 al mes",
            "tenemos ahorros de €300,000",
            "queremos vivir en Florida",
            "nos gusta el clima cálido",
            "¿qué visa necesitamos?",
            "¿podemos comprar una casa?",
        ],
    },
    # Plan 6: Artista
    {
        "name": "Artist",
        "persona": "Músico, 30 años, Brasil, quiere carrera en LA",
        "steps": [
            "oi, falo español también",
            "soy músico profesional",
            "me llamo Lucas Silva",
            "soy brasileño, de São Paulo",
            "tengo 30 años",
            "toco guitarra y canto",
            "tengo un álbum publicado",
            "quiero desarrollar mi carrera en Los Angeles",
            "viajo solo por ahora",
            "tengo $15,000 ahorrados",
            "¿hay visa para artistas?",
            "¿cómo funciona?",
        ],
    },
    # Plan 7: Enfermera
    {
        "name": "Nurse",
        "persona": "Enfermera, 32 años, Filipinas, quiere trabajar en hospital",
        "steps": [
            "hello, I speak Spanish too",
            "hola, soy enfermera",
            "me llamo Maria Santos",
            "soy de Filipinas pero hablo español",
            "tengo 32 años",
            "tengo 8 años de experiencia en UCI",
            "quiero trabajar en un hospital en USA",
            "viajo sola",
            "tengo $10,000 ahorrados",
            "¿hay demanda de enfermeras?",
            "¿qué certificaciones necesito?",
        ],
    },
    # Plan 8: Deportista
    {
        "name": "Athlete",
        "persona": "Futbolista, 24 años, Colombia, fichado por equipo MLS",
        "steps": [
            "hola",
            "soy futbolista profesional",
            "me llamo Diego Ramírez",
            "soy colombiano",
            "tengo 24 años",
            "juego en la primera división de Colombia",
            "un equipo de la MLS me quiere fichar",
            "¿qué visa necesito?",
            "¿puedo llevar a mi novia?",
            "ella es mi prometida",
        ],
    },
    # Plan 9: Investigador
    {
        "name": "Researcher",
        "persona": "PhD, 40 años, Chile, oferta en universidad",
        "steps": [
            "buenas tardes",
            "soy investigador científico",
            "me llamo Alejandro Muñoz",
            "soy chileno",
            "tengo 40 años",
            "tengo un PhD en biología molecular",
            "me ofrecieron un puesto en MIT",
            "viajo con mi esposa y un hijo de 3 años",
            "mi esposa también es científica",
            "¿qué visa aplica para investigadores?",
        ],
    },
    # Plan 10: Chef
    {
        "name": "Chef",
        "persona": "Chef, 35 años, Perú, quiere abrir restaurante",
        "steps": [
            "hola",
            "soy chef profesional",
            "me llamo Pedro Quispe",
            "soy peruano, de Lima",
            "tengo 35 años",
            "tengo 15 años de experiencia",
            "trabajé en restaurantes con estrella Michelin",
            "quiero abrir mi propio restaurante en Miami",
            "tengo $100,000 para invertir",
            "viajo con mi esposa",
            "¿qué visa necesito?",
        ],
    },
    # Plan 11: Con correcciones
    {
        "name": "With Corrections",
        "persona": "Usuario que corrige información",
        "steps": [
            "hola",
            "me llamo Juan",
            "no, perdón, me llamo Pedro",
            "soy de México",
            "en realidad soy de Guatemala",
            "tengo 30 años",
            "corrijo: tengo 32 años",
            "soy ingeniero",
            "quiero migrar a USA",
        ],
    },
    # Plan 12: Preguntas primero
    {
        "name": "Questions First",
        "persona": "Usuario que pregunta antes de dar datos",
        "steps": [
            "hola",
            "¿cuánto cuesta el proceso de migración?",
            "¿cuánto tiempo toma?",
            "¿qué documentos necesito?",
            "ok, entiendo",
            "me llamo Laura",
            "soy de Ecuador",
            "tengo 28 años",
            "soy contadora",
        ],
    },
    # Plan 13: Respuestas cortas
    {
        "name": "Short Answers",
        "persona": "Usuario de pocas palabras",
        "steps": [
            "hola",
            "migrar",
            "Carlos",
            "Colombia",
            "35",
            "ingeniero",
            "soltero",
            "sí",
            "trabajo",
            "6 meses",
        ],
    },
    # Plan 14: Información completa de golpe
    {
        "name": "Complete Info at Once",
        "persona": "Usuario que da toda la info de una vez",
        "steps": [
            "Hola, soy María González, tengo 33 años, soy de Argentina, trabajo como diseñadora gráfica, gano $3000 al mes, estoy casada y tengo un hijo de 5 años, tenemos $40,000 ahorrados y queremos migrar a Estados Unidos en los próximos 12 meses porque queremos mejores oportunidades para nuestro hijo",
            "¿qué visa nos conviene?",
            "¿qué ciudades recomiendas para familias?",
        ],
    },
    # Plan 15: Cambio de planes
    {
        "name": "Change of Plans",
        "persona": "Usuario que cambia de opinión",
        "steps": [
            "hola, quiero migrar a Canadá",
            "ah no, mejor a Estados Unidos",
            "me llamo Roberto",
            "soy de Chile",
            "tengo 40 años",
            "primero pensé en visa de turista",
            "pero mejor visa de trabajo",
            "soy arquitecto",
        ],
    },
    # Plan 16: Urgencia
    {
        "name": "Urgent Case",
        "persona": "Usuario con urgencia",
        "steps": [
            "necesito ayuda urgente",
            "tengo que salir de mi país ya",
            "me llamo José",
            "soy de Nicaragua",
            "tengo 45 años",
            "la situación política está muy mal",
            "tengo familia en Miami",
            "¿qué puedo hacer?",
            "tengo $5,000",
        ],
    },
    # Plan 17: Reunificación familiar
    {
        "name": "Family Reunification",
        "persona": "Usuario con familia en USA",
        "steps": [
            "hola",
            "mi hermano vive en Estados Unidos",
            "él es ciudadano americano",
            "me llamo Carmen",
            "soy de República Dominicana",
            "tengo 50 años",
            "quiero reunirme con mi hermano",
            "¿él puede patrocinarme?",
            "¿cuánto tiempo toma?",
        ],
    },
    # Plan 18: Inversionista
    {
        "name": "Investor",
        "persona": "Inversionista con capital",
        "steps": [
            "buenas",
            "quiero invertir en Estados Unidos",
            "me llamo Ricardo Salazar",
            "soy de Panamá",
            "tengo 55 años",
            "tengo $1,000,000 para invertir",
            "quiero la visa de inversionista",
            "¿qué tipo de negocio me recomiendas?",
            "viajo con mi esposa",
        ],
    },
    # Plan 19: Transferencia interna
    {
        "name": "Internal Transfer",
        "persona": "Empleado de multinacional",
        "steps": [
            "hola",
            "trabajo en una empresa multinacional",
            "me llamo Fernando Torres",
            "soy de España",
            "tengo 38 años",
            "soy gerente de ventas",
            "mi empresa tiene oficinas en USA",
            "quieren transferirme a Nueva York",
            "viajo con mi esposa y 2 hijos",
            "¿qué visa necesito?",
        ],
    },
    # Plan 20: Caso complejo
    {
        "name": "Complex Case",
        "persona": "Caso con múltiples factores",
        "steps": [
            "hola, mi caso es un poco complicado",
            "me llamo Andrés Morales",
            "soy de Venezuela pero vivo en Colombia hace 3 años",
            "tengo 42 años",
            "soy abogado pero aquí trabajo como consultor",
            "mi esposa es colombiana",
            "tenemos 2 hijos: uno venezolano y uno colombiano",
            "tenemos $50,000 ahorrados",
            "queremos migrar a USA",
            "¿qué opciones tenemos?",
            "¿afecta que yo sea venezolano?",
        ],
    },
]


# ============== SIMULADOR ==============


class HumanSimulator:
    """Simula conversaciones tipo humano"""

    def __init__(self):
        self.results: list[SimulationResult] = []
        self.total_inputs = 0
        self.total_responses = 0
        self.crashes = 0
        self.silent_failures = 0
        self.response_times: list[float] = []
        self.friction_counts: dict[str, int] = {}

    def simulate_input(self, text: str) -> tuple[bool, float, str | None]:
        """
        Simula un input y verifica respuesta.
        Returns: (responded, response_time_ms, error)
        """
        start_time = time.time()

        try:
            # Interpretar input
            interpreted = interpret_user_input(text, "")

            response_time = (time.time() - start_time) * 1000

            # Verificar que hay respuesta
            if interpreted is None:
                return False, response_time, "No interpretation"

            # Si es UNKNOWN, verificar fallback
            if interpreted.input_type == InputType.UNKNOWN and not interpreted.extracted_data:
                fallback = get_empathic_fallback()
                response = fallback.get_phase_fallback("unknown", "es")
                if not response:
                    return False, response_time, "No fallback response"

            return True, response_time, None

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.crashes += 1
            return False, response_time, str(e)

    def run_plan(self, plan: dict[str, Any], plan_id: int) -> SimulationResult:
        """Ejecuta un plan completo"""
        result = SimulationResult(
            flow_id=plan_id,
            flow_name=plan["name"],
            completed=False,
            steps_total=len(plan["steps"]),
            steps_completed=0,
        )

        for step in plan["steps"]:
            self.total_inputs += 1

            responded, response_time, error = self.simulate_input(step)
            result.response_times.append(response_time)
            self.response_times.append(response_time)

            if responded:
                self.total_responses += 1
                result.steps_completed += 1
            else:
                self.silent_failures += 1
                result.errors.append(f"Step '{step[:30]}...': {error}")

                # Registrar fricción
                friction = f"No response to: {step[:50]}"
                self.friction_counts[friction] = self.friction_counts.get(friction, 0) + 1
                result.friction_points.append(friction)

        result.completed = result.steps_completed == result.steps_total
        return result

    def run_all_plans(self) -> list[SimulationResult]:
        """Ejecuta todos los planes"""
        print("\n" + "=" * 60)
        print("🧪 SIMULACIÓN DE 20 PLANES TIPO HUMANO")
        print("=" * 60)

        for i, plan in enumerate(HUMAN_SIMULATION_PLANS, 1):
            print(f"\n📋 Plan {i}/20: {plan['name']}")
            print(f"   Persona: {plan['persona']}")
            print(f"   Steps: {len(plan['steps'])}")

            result = self.run_plan(plan, i)
            self.results.append(result)

            status = "✅" if result.completed else "❌"
            print(f"   {status} Completed: {result.steps_completed}/{result.steps_total}")

            if result.errors:
                for error in result.errors[:2]:
                    print(f"      ⚠️ {error[:60]}...")

        return self.results

    def get_metrics(self) -> dict[str, Any]:
        """Obtiene métricas de la simulación"""
        completed_plans = sum(1 for r in self.results if r.completed)

        return {
            "total_inputs": self.total_inputs,
            "total_responses": self.total_responses,
            "response_rate": (self.total_responses / self.total_inputs * 100) if self.total_inputs > 0 else 0,
            "avg_response_time_ms": (
                sum(self.response_times) / len(self.response_times) if self.response_times else 0
            ),
            "crashes": self.crashes,
            "silent_failures": self.silent_failures,
            "plans_completed": completed_plans,
            "plans_total": len(self.results),
            "top_frictions": sorted(self.friction_counts.items(), key=lambda x: -x[1])[:10],
        }


# ============== RELEASE GATE ==============


class ReleaseGate:
    """Gate de release que bloquea si falla cualquier criterio"""

    def __init__(self):
        self.report = ReleaseReport(
            timestamp=datetime.now(),
            version=self._get_version(),
            response_rate=0,
            avg_response_time_ms=0,
            total_inputs=0,
            total_responses=0,
            crashes=0,
            silent_failures=0,
            plans_completed=0,
            plans_total=REQUIRED_COMPLETE_PLANS,
            tests_passed=0,
            tests_total=0,
        )

    def _get_version(self) -> str:
        """Obtiene la versión del proyecto"""
        try:
            version_file = Path(__file__).parent.parent / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
        except:
            pass
        return datetime.now().strftime("%Y.%m.%d")

    def run_module_tests(self) -> list[TestMetrics]:
        """Ejecuta tests de módulos"""
        print("\n" + "=" * 60)
        print("📦 VERIFICACIÓN DE MÓDULOS")
        print("=" * 60)

        results = []
        modules = [
            "app.services.never_silent",
            "app.services.flow_governor",
            "app.services.memory_profiler",
            "app.services.availability_watchdog",
        ]

        for module in modules:
            start = time.time()
            try:
                __import__(module)
                duration = (time.time() - start) * 1000
                results.append(TestMetrics(name=f"Import {module}", passed=True, duration_ms=duration))
                print(f"  ✅ {module}")
            except Exception as e:
                duration = (time.time() - start) * 1000
                results.append(
                    TestMetrics(name=f"Import {module}", passed=False, duration_ms=duration, errors=[str(e)])
                )
                print(f"  ❌ {module}: {e}")

        return results

    def run_hard_rules_tests(self) -> list[TestMetrics]:
        """Ejecuta tests de reglas duras"""
        print("\n" + "=" * 60)
        print("🧪 TESTS DE REGLAS DURAS")
        print("=" * 60)

        # Importar y ejecutar tests
        try:
            from tests.test_hard_rules_blocking import (
                test_20_complete_flows,
                test_fuzz_100_random_inputs,
                test_rule_1_always_respond,
                test_rule_1_callback_response,
                test_rule_2_form_throttling,
                test_rule_3_visa_without_context,
                test_rule_4_understanding_required,
                test_rule_5_corrections_not_ignored,
                test_rule_6_markdown_valid,
            )

            tests = [
                ("Rule 1: Always Respond", test_rule_1_always_respond),
                ("Rule 1b: Callbacks", test_rule_1_callback_response),
                ("Rule 2: Form Throttling", test_rule_2_form_throttling),
                ("Rule 3: Visa Context", test_rule_3_visa_without_context),
                ("Rule 4: Understanding", test_rule_4_understanding_required),
                ("Rule 5: Corrections", test_rule_5_corrections_not_ignored),
                ("Rule 6: Markdown", test_rule_6_markdown_valid),
                ("Fuzz 100 Inputs", test_fuzz_100_random_inputs),
                ("20 Flows", test_20_complete_flows),
            ]

            results = []
            for name, test_func in tests:
                start = time.time()
                try:
                    result = test_func()
                    duration = (time.time() - start) * 1000
                    results.append(
                        TestMetrics(
                            name=name,
                            passed=result.passed,
                            duration_ms=duration,
                            details={"message": result.message},
                            errors=result.details if not result.passed else [],
                        )
                    )
                except Exception as e:
                    duration = (time.time() - start) * 1000
                    results.append(
                        TestMetrics(name=name, passed=False, duration_ms=duration, errors=[str(e)])
                    )

            return results

        except ImportError as e:
            print(f"  ❌ Could not import tests: {e}")
            return [TestMetrics(name="Import Tests", passed=False, duration_ms=0, errors=[str(e)])]

    def run_simulations(self) -> tuple[list[SimulationResult], dict[str, Any]]:
        """Ejecuta simulaciones tipo humano"""
        simulator = HumanSimulator()
        results = simulator.run_all_plans()
        metrics = simulator.get_metrics()
        return results, metrics

    def check_manual_test(self) -> tuple[bool, str]:
        """Verifica si hay evidencia de test manual"""
        manual_test_file = Path(__file__).parent.parent / "data" / "manual_test_evidence.json"

        if manual_test_file.exists():
            try:
                with open(manual_test_file) as f:
                    evidence = json.load(f)

                if evidence.get("completed") and evidence.get("plan_maestro_completed"):
                    return True, evidence.get("notes", "Manual test completed")
            except:
                pass

        return False, "No manual test evidence found"

    def evaluate_release(self) -> bool:
        """Evalúa si se puede hacer release"""
        blocking = []

        # Verificar crashes
        if self.report.crashes > MAX_CRASHES:
            blocking.append(f"Crashes: {self.report.crashes} (max: {MAX_CRASHES})")

        # Verificar silent failures
        if self.report.silent_failures > MAX_SILENT:
            blocking.append(f"Silent failures: {self.report.silent_failures} (max: {MAX_SILENT})")

        # Verificar tasa de respuesta
        if self.report.response_rate < REQUIRED_RESPONSE_RATE:
            blocking.append(
                f"Response rate: {self.report.response_rate:.1f}% (required: {REQUIRED_RESPONSE_RATE}%)"
            )

        # Verificar planes completos
        if self.report.plans_completed < REQUIRED_COMPLETE_PLANS:
            blocking.append(f"Plans completed: {self.report.plans_completed}/{REQUIRED_COMPLETE_PLANS}")

        # Verificar tests
        if self.report.tests_passed < self.report.tests_total:
            blocking.append(f"Tests: {self.report.tests_passed}/{self.report.tests_total} passed")

        # Verificar test manual
        if not self.report.manual_test_completed:
            blocking.append("Manual test in Telegram not completed")

        self.report.blocking_reasons = blocking
        self.report.can_release = len(blocking) == 0

        return self.report.can_release

    def generate_report(self) -> str:
        """Genera reporte markdown"""
        lines = [
            "# 🚀 MigPAL Release Report",
            "",
            f"**Fecha:** {self.report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Versión:** {self.report.version}",
            "",
            "---",
            "",
            "## 📊 Resumen Ejecutivo",
            "",
            "| Métrica | Valor | Requerido | Estado |",
            "|---------|-------|-----------|--------|",
            f"| Tasa de Respuesta | {self.report.response_rate:.1f}% | {REQUIRED_RESPONSE_RATE}% | {'✅' if self.report.response_rate >= REQUIRED_RESPONSE_RATE else '❌'} |",
            f"| Tiempo Medio | {self.report.avg_response_time_ms:.1f}ms | <1000ms | {'✅' if self.report.avg_response_time_ms < 1000 else '⚠️'} |",
            f"| Crashes | {self.report.crashes} | {MAX_CRASHES} | {'✅' if self.report.crashes <= MAX_CRASHES else '❌'} |",
            f"| Silent Failures | {self.report.silent_failures} | {MAX_SILENT} | {'✅' if self.report.silent_failures <= MAX_SILENT else '❌'} |",
            f"| Planes Completos | {self.report.plans_completed}/{self.report.plans_total} | {REQUIRED_COMPLETE_PLANS}/{REQUIRED_COMPLETE_PLANS} | {'✅' if self.report.plans_completed >= REQUIRED_COMPLETE_PLANS else '❌'} |",
            f"| Tests Pasados | {self.report.tests_passed}/{self.report.tests_total} | {self.report.tests_total}/{self.report.tests_total} | {'✅' if self.report.tests_passed >= self.report.tests_total else '❌'} |",
            f"| Test Manual | {'Sí' if self.report.manual_test_completed else 'No'} | Sí | {'✅' if self.report.manual_test_completed else '❌'} |",
            "",
            "---",
            "",
            "## 🎯 Decisión de Release",
            "",
        ]

        if self.report.can_release:
            lines.extend(
                [
                    "### ✅ APROBADO PARA RELEASE",
                    "",
                    "Todos los criterios de calidad han sido cumplidos.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "### ❌ BLOQUEADO - NO RELEASE",
                    "",
                    "**Razones de bloqueo:**",
                    "",
                ]
            )
            for reason in self.report.blocking_reasons:
                lines.append(f"- ⛔ {reason}")
            lines.append("")

        # Tests
        lines.extend(
            [
                "---",
                "",
                "## 🧪 Resultados de Tests",
                "",
                "| Test | Estado | Tiempo |",
                "|------|--------|--------|",
            ]
        )

        for test in self.report.test_results:
            status = "✅" if test.passed else "❌"
            lines.append(f"| {test.name} | {status} | {test.duration_ms:.0f}ms |")

        # Simulaciones
        lines.extend(
            [
                "",
                "---",
                "",
                "## 📋 Simulaciones de Planes",
                "",
                "| # | Plan | Pasos | Estado |",
                "|---|------|-------|--------|",
            ]
        )

        for sim in self.report.simulations:
            status = "✅" if sim.completed else "❌"
            lines.append(
                f"| {sim.flow_id} | {sim.flow_name} | {sim.steps_completed}/{sim.steps_total} | {status} |"
            )

        # Fricciones
        if self.report.top_frictions:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## ⚠️ Top Fricciones",
                    "",
                ]
            )
            for friction, count in self.report.top_frictions[:5]:
                lines.append(f"- ({count}x) {friction}")

        # Bugs
        lines.extend(
            [
                "",
                "---",
                "",
                "## 🐛 Bugs",
                "",
                "### Encontrados",
                "",
            ]
        )

        if self.report.bugs_found:
            for bug in self.report.bugs_found:
                lines.append(f"- 🔴 {bug}")
        else:
            lines.append("- Ninguno en esta ejecución")

        lines.extend(
            [
                "",
                "### Cerrados",
                "",
            ]
        )

        if self.report.bugs_closed:
            for bug in self.report.bugs_closed:
                lines.append(f"- 🟢 {bug}")
        else:
            lines.append("- N/A")

        # Footer
        lines.extend(
            [
                "",
                "---",
                "",
                "*Generado automáticamente por release_gate.py*",
                "",
            ]
        )

        return "\n".join(lines)

    def run(self) -> int:
        """Ejecuta el gate completo"""
        print("\n" + "=" * 70)
        print("🚦 MIGPAL RELEASE GATE - SEGMENTO 4/4")
        print("=" * 70)
        print(f"Fecha: {self.report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Versión: {self.report.version}")
        print("=" * 70)

        # 1. Tests de módulos
        module_tests = self.run_module_tests()
        self.report.test_results.extend(module_tests)

        # 2. Tests de reglas duras
        hard_tests = self.run_hard_rules_tests()
        self.report.test_results.extend(hard_tests)

        # Contar tests
        self.report.tests_total = len(self.report.test_results)
        self.report.tests_passed = sum(1 for t in self.report.test_results if t.passed)

        # 3. Simulaciones
        simulations, metrics = self.run_simulations()
        self.report.simulations = simulations
        self.report.response_rate = metrics["response_rate"]
        self.report.avg_response_time_ms = metrics["avg_response_time_ms"]
        self.report.total_inputs = metrics["total_inputs"]
        self.report.total_responses = metrics["total_responses"]
        self.report.crashes = metrics["crashes"]
        self.report.silent_failures = metrics["silent_failures"]
        self.report.plans_completed = metrics["plans_completed"]
        self.report.top_frictions = metrics["top_frictions"]

        # 4. Verificar test manual
        manual_completed, manual_notes = self.check_manual_test()
        self.report.manual_test_completed = manual_completed
        self.report.manual_test_notes = manual_notes

        # 5. Evaluar release
        can_release = self.evaluate_release()

        # 6. Generar reporte
        report_content = self.generate_report()

        # Guardar reporte
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORT_FILE, "w") as f:
            f.write(report_content)

        # Mostrar resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN FINAL")
        print("=" * 70)
        print(f"Tasa de Respuesta: {self.report.response_rate:.1f}%")
        print(f"Tiempo Medio: {self.report.avg_response_time_ms:.1f}ms")
        print(f"Crashes: {self.report.crashes}")
        print(f"Silent Failures: {self.report.silent_failures}")
        print(f"Planes Completos: {self.report.plans_completed}/{self.report.plans_total}")
        print(f"Tests: {self.report.tests_passed}/{self.report.tests_total}")
        print(f"Test Manual: {'✅' if self.report.manual_test_completed else '❌'}")
        print()
        print(f"📄 Reporte guardado en: {REPORT_FILE}")
        print()

        if can_release:
            print("=" * 70)
            print("✅ RELEASE APROBADO")
            print("=" * 70)
            return 0
        else:
            print("=" * 70)
            print("❌ RELEASE BLOQUEADO")
            print("=" * 70)
            print("\nRazones de bloqueo:")
            for reason in self.report.blocking_reasons:
                print(f"  ⛔ {reason}")
            return 1


# ============== MAIN ==============


def main():
    gate = ReleaseGate()
    exit_code = gate.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
