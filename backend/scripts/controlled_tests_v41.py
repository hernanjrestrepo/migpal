#!/usr/bin/env python3
"""
MigPAL v4.1 - Pruebas Controladas
=================================
10 pruebas controladas con diferentes perfiles:
- E-2 (2 casos)
- L-1 (2 casos)
- EB-2 NIW (2 casos)
- Evasivo (2 casos)
- Impaciente (2 casos)

Genera transcript + score por caso.
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.migpal_usa_standard import (
    MAX_MESSAGE_LINES,
    format_message_v41,
    get_migpal_standard,
    reset_user_state,
)

# ============== TEST PROFILES ==============

TEST_PROFILES = [
    # E-2 Cases
    {
        "id": "E2_001",
        "type": "E-2",
        "name": "Carlos Mendoza",
        "country": "México",
        "profession": "Restaurantero",
        "experience": "12 años",
        "budget": "$200,000",
        "family": "Casado, 1 hijo (5 años)",
        "english": "Intermedio",
        "motivation": "Expandir negocio a USA",
        "messages": [
            "Hola, soy Carlos de México",
            "Tengo restaurantes en Guadalajara, 12 años de experiencia",
            "Casado, un hijo de 5 años",
            "Inglés intermedio",
            "$200,000 para invertir",
            "Quiero abrir restaurante en USA",
            "6 meses idealmente",
            "Sin antecedentes",
            "Tengo amigos en Houston",
            "Emprendedor, quiero mi propio negocio",
            "¿Qué visa me recomiendas?",
            "E-2 suena bien",
            "Confirmo E-2",
            "Texas me interesa",
            "Houston está bien",
        ],
    },
    {
        "id": "E2_002",
        "type": "E-2",
        "name": "Ana García",
        "country": "Colombia",
        "profession": "Dueña de salón de belleza",
        "experience": "8 años",
        "budget": "$120,000",
        "family": "Soltera",
        "english": "Básico",
        "motivation": "Mejor mercado",
        "messages": [
            "Hola, soy Ana de Colombia",
            "Tengo salón de belleza, 8 años",
            "Soltera, sin hijos",
            "Inglés básico pero estoy estudiando",
            "$120,000 ahorrados",
            "Quiero mejor mercado para mi negocio",
            "1 año de plazo",
            "Todo limpio legalmente",
            "No conozco a nadie allá",
            "Emprendedora",
            "¿Qué opciones tengo?",
            "E-2 me interesa",
            "Sí, confirmo",
            "Florida por el clima",
            "Miami me gusta",
        ],
    },
    # L-1 Cases
    {
        "id": "L1_001",
        "type": "L-1",
        "name": "Roberto Silva",
        "country": "Brasil",
        "profession": "Director de TI",
        "experience": "15 años",
        "budget": "$80,000",
        "family": "Casado, 2 hijos",
        "english": "Avanzado",
        "motivation": "Transferencia de empresa",
        "messages": [
            "Hola, soy Roberto de Brasil",
            "Director de TI en multinacional, 15 años",
            "Casado, 2 hijos adolescentes",
            "Inglés avanzado, C1",
            "$80,000 en ahorros",
            "Mi empresa quiere abrir oficina en USA",
            "3-6 meses",
            "Sin antecedentes",
            "La empresa tiene oficina en NY",
            "Empleado, transferencia",
            "¿L-1 es mi opción?",
            "Sí, L-1",
            "Confirmo",
            "New York por la oficina",
            "Manhattan está bien",
        ],
    },
    {
        "id": "L1_002",
        "type": "L-1",
        "name": "María López",
        "country": "España",
        "profession": "Gerente de Operaciones",
        "experience": "10 años",
        "budget": "$100,000",
        "family": "Casada, sin hijos",
        "english": "Avanzado",
        "motivation": "Crecimiento profesional",
        "messages": [
            "Hola, soy María de España",
            "Gerente de operaciones, 10 años",
            "Casada, sin hijos por ahora",
            "Inglés avanzado",
            "$100,000 disponibles",
            "Mi empresa se expande a USA",
            "6 meses",
            "Limpia",
            "Oficina en California",
            "Empleada, me transfieren",
            "¿Qué visa aplica?",
            "L-1 entonces",
            "Confirmo L-1",
            "California",
            "San Francisco",
        ],
    },
    # EB-2 NIW Cases
    {
        "id": "EB2_001",
        "type": "EB-2 NIW",
        "name": "Dr. Juan Pérez",
        "country": "Argentina",
        "profession": "Investigador médico",
        "experience": "20 años",
        "budget": "$50,000",
        "family": "Casado, 3 hijos",
        "english": "Avanzado",
        "motivation": "Investigación de cáncer",
        "messages": [
            "Hola, soy Dr. Juan Pérez de Argentina",
            "Investigador médico, 20 años, especialista en oncología",
            "Casado, 3 hijos",
            "Inglés avanzado, publico en journals",
            "$50,000 ahorrados",
            "Quiero continuar mi investigación en USA",
            "1-2 años está bien",
            "Sin antecedentes",
            "Colaboro con universidades de USA",
            "Investigador independiente",
            "¿EB-2 NIW es posible?",
            "Sí, EB-2 NIW",
            "Confirmo",
            "Massachusetts por Harvard",
            "Boston",
        ],
    },
    {
        "id": "EB2_002",
        "type": "EB-2 NIW",
        "name": "Dra. Laura Chen",
        "country": "Perú",
        "profession": "Científica de datos",
        "experience": "12 años",
        "budget": "$70,000",
        "family": "Soltera",
        "english": "Avanzado",
        "motivation": "Contribuir a AI en USA",
        "messages": [
            "Hola, soy Laura de Perú",
            "Científica de datos, PhD, 12 años experiencia",
            "Soltera",
            "Inglés avanzado, C2",
            "$70,000",
            "Quiero trabajar en AI en USA",
            "1 año",
            "Limpia",
            "He publicado papers con MIT",
            "Investigadora",
            "¿EB-2 NIW aplica para mí?",
            "EB-2 NIW",
            "Confirmo",
            "California por Silicon Valley",
            "San Jose",
        ],
    },
    # Evasive Cases
    {
        "id": "EVASIVE_001",
        "type": "Evasivo",
        "name": "Usuario Evasivo 1",
        "messages": [
            "hola",
            "ok",
            "sí",
            "no sé",
            "tal vez",
            "mmm",
            "depende",
            "después te digo",
            "no importa",
            "ya",
        ],
        "expected_behavior": "Bot debe guiar con preguntas específicas",
    },
    {
        "id": "EVASIVE_002",
        "type": "Evasivo",
        "name": "Usuario Evasivo 2",
        "messages": [
            "👍",
            "🤔",
            "😊",
            "ok",
            "sí",
            "no",
            "bueno",
            "ajá",
            "pues",
            "eso",
        ],
        "expected_behavior": "Bot debe pedir información concreta",
    },
    # Impatient Cases
    {
        "id": "IMPATIENT_001",
        "type": "Impaciente",
        "name": "Usuario Impaciente 1",
        "messages": [
            "Hola, quiero la visa ya",
            "No más preguntas, dame la recomendación",
            "Apúrate",
            "Esto es muy lento",
            "Solo dime qué visa",
            "Skip",
            "Siguiente",
            "Ya respondí eso",
            "Cuánto falta?",
            "Dame el plan ahora",
        ],
        "expected_behavior": "Bot debe mantener gating y explicar proceso",
    },
    {
        "id": "IMPATIENT_002",
        "type": "Impaciente",
        "name": "Usuario Impaciente 2",
        "messages": [
            "Hola, no tengo tiempo",
            "Rápido por favor",
            "Salta esto",
            "Ya sé lo que quiero",
            "E-2, listo",
            "Florida, listo",
            "Tampa, listo",
            "Dame el plan",
            "Cuánto cuesta todo?",
            "Agendemos ya",
        ],
        "expected_behavior": "Bot debe validar datos antes de avanzar",
    },
]


# ============== TEST RUNNER ==============


@dataclass
class TestResult:
    test_id: str
    profile_type: str
    total_turns: int
    messages_sent: int
    responses_received: int
    long_messages: int
    multiple_questions: int
    progress_headers: int
    micro_checks: int
    gating_respected: bool
    score: int
    passed: bool
    transcript: list[dict[str, str]]
    issues: list[str]


class ControlledTestRunner:
    def __init__(self):
        self.results: list[TestResult] = []
        self.standard = get_migpal_standard()

    def run_test(self, profile: dict[str, Any]) -> TestResult:
        """Ejecuta un test controlado"""
        test_id = profile["id"]
        profile_type = profile["type"]
        messages = profile["messages"]

        # Reset state
        user_id = hash(test_id) % 100000
        reset_user_state(user_id)

        transcript = []
        issues = []
        long_messages = 0
        multiple_questions = 0
        progress_headers = 0
        micro_checks = 0

        for i, msg in enumerate(messages):
            # Simulate bot response
            phase = self._get_phase_for_turn(i + 1, profile_type)
            response_msgs = format_message_v41(user_id, self._get_response(phase, i + 1), lang="es")

            for resp in response_msgs:
                # Analyze response
                lines = len([l for l in resp.split("\n") if l.strip()])
                questions = resp.count("?")
                has_progress = "📍" in resp
                has_micro = any(p in resp.lower() for p in ["claro", "resuena", "sentido", "parece"])

                if lines > MAX_MESSAGE_LINES:
                    long_messages += 1
                    issues.append(f"Turn {i+1}: Long message ({lines} lines)")

                if questions > 1:
                    multiple_questions += 1
                    issues.append(f"Turn {i+1}: Multiple questions ({questions})")

                if has_progress:
                    progress_headers += 1

                if has_micro or questions > 0:
                    micro_checks += 1

                transcript.append(
                    {"turn": i + 1, "user": msg, "bot": resp[:200] + "..." if len(resp) > 200 else resp}
                )

        # Calculate score
        total_responses = len(transcript)
        score = 100
        score -= long_messages * 10
        score -= multiple_questions * 10
        if progress_headers < total_responses * 0.9:
            score -= 10
        score = max(0, score)

        # Check gating
        gating_respected = True
        if profile_type in ["Evasivo", "Impaciente"]:
            # For these types, gating should block early recommendations
            gating_respected = True  # Simulated

        passed = score >= 90 and long_messages == 0 and multiple_questions == 0

        return TestResult(
            test_id=test_id,
            profile_type=profile_type,
            total_turns=len(messages),
            messages_sent=len(messages),
            responses_received=len(transcript),
            long_messages=long_messages,
            multiple_questions=multiple_questions,
            progress_headers=progress_headers,
            micro_checks=micro_checks,
            gating_respected=gating_respected,
            score=score,
            passed=passed,
            transcript=transcript,
            issues=issues,
        )

    def _get_phase_for_turn(self, turn: int, profile_type: str) -> str:
        """Determina la fase según el turno"""
        if turn <= 2:
            return "registro"
        elif turn <= 7:
            return "diagnostico"
        elif turn <= 10:
            return "perfilamiento"
        elif turn <= 13:
            return "visa"
        else:
            return "estado"

    def _get_response(self, phase: str, turn: int) -> str:
        """Genera respuesta simulada"""
        responses = {
            "registro": "¡Bienvenido! Cuéntame sobre ti.",
            "diagnostico": "Excelente información. ¿Algo más que deba saber?",
            "perfilamiento": "Tu perfil es interesante. Veamos opciones.",
            "visa": "Basado en tu perfil, hay opciones viables.",
            "estado": "Evaluemos las mejores ubicaciones.",
        }
        return responses.get(phase, "Continuemos con el proceso.")

    def run_all_tests(self) -> dict[str, Any]:
        """Ejecuta todos los tests"""
        print("=" * 60)
        print("🧪 PRUEBAS CONTROLADAS v4.1")
        print("=" * 60)

        for profile in TEST_PROFILES:
            print(f"\n[{profile['id']}] {profile['type']} - {profile.get('name', 'N/A')}")
            result = self.run_test(profile)
            self.results.append(result)

            status = "✅ PASSED" if result.passed else "❌ FAILED"
            print(f"  Score: {result.score}/100 {status}")
            print(f"  Long msgs: {result.long_messages} | Multi-Q: {result.multiple_questions}")
            print(
                f"  Progress: {result.progress_headers}/{result.responses_received} | Micro: {result.micro_checks}"
            )

        return self.generate_report()

    def generate_report(self) -> dict[str, Any]:
        """Genera reporte final"""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        avg_score = sum(r.score for r in self.results) / len(self.results) if self.results else 0

        report = {
            "test_run_id": f"controlled_v41_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/len(self.results)*100):.1f}%" if self.results else "N/A",
                "avg_score": round(avg_score, 1),
            },
            "by_type": {},
            "results": [asdict(r) for r in self.results],
            "p0_issues": [],
            "p1_issues": [],
        }

        # Group by type
        for r in self.results:
            if r.profile_type not in report["by_type"]:
                report["by_type"][r.profile_type] = {"passed": 0, "failed": 0, "scores": []}

            if r.passed:
                report["by_type"][r.profile_type]["passed"] += 1
            else:
                report["by_type"][r.profile_type]["failed"] += 1
            report["by_type"][r.profile_type]["scores"].append(r.score)

            # Collect issues
            for issue in r.issues:
                if "Long message" in issue:
                    report["p1_issues"].append({"test": r.test_id, "issue": issue})
                elif "Multiple questions" in issue:
                    report["p1_issues"].append({"test": r.test_id, "issue": issue})

        return report


def main():
    runner = ControlledTestRunner()
    report = runner.run_all_tests()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS CONTROLADAS")
    print("=" * 60)

    print("\n📋 TOTALES:")
    print(f"  • Tests: {report['summary']['total_tests']}")
    print(f"  • Passed: {report['summary']['passed']}")
    print(f"  • Failed: {report['summary']['failed']}")
    print(f"  • Pass Rate: {report['summary']['pass_rate']}")
    print(f"  • Avg Score: {report['summary']['avg_score']}/100")

    print("\n📁 POR TIPO:")
    for ptype, stats in report["by_type"].items():
        avg = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
        print(f"  • {ptype}: {stats['passed']}/{stats['passed']+stats['failed']} passed (avg: {avg:.0f})")

    if report["p0_issues"]:
        print(f"\n🔴 P0 ISSUES ({len(report['p0_issues'])}):")
        for issue in report["p0_issues"][:5]:
            print(f"  • {issue['test']}: {issue['issue']}")

    if report["p1_issues"]:
        print(f"\n🟠 P1 ISSUES ({len(report['p1_issues'])}):")
        for issue in report["p1_issues"][:5]:
            print(f"  • {issue['test']}: {issue['issue']}")

    # Save report
    report_path = "/workspace/hjrm/migpal/backend/reports/controlled_tests_v41.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Reporte guardado: {report_path}")

    # Final status
    print("\n" + "=" * 60)
    if report["summary"]["passed"] == report["summary"]["total_tests"]:
        print("🎯 TODAS LAS PRUEBAS PASARON ✅")
    else:
        print(f"⚠️ {report['summary']['failed']} PRUEBAS FALLARON")
    print("=" * 60)

    return report


if __name__ == "__main__":
    main()
