#!/usr/bin/env python3
"""
MigPAL USA - Simulación E2E de 20 Conversaciones
=================================================
Simula 20 conversaciones completas para validar el estándar MigPAL USA.

Perfiles de prueba:
- 5 perfiles E-2 (emprendedor/inversionista)
- 5 perfiles L-1 (transferencia corporativa)
- 5 perfiles EB-2 NIW (profesional destacado)
- 5 perfiles mixtos (evaluando opciones)

Métricas a evaluar:
- Cumplimiento de reglas conversacionales
- Gating de visa (perfil + resumen)
- Uso de matrices ponderadas
- Micro-checks
- Formularios (máx 1/5 turnos)
- Fricciones detectadas
"""

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

# Agregar path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.migpal_usa_standard import FORBIDDEN_PHRASES, check_visa_gating, get_migpal_standard

# ============== PERFILES DE PRUEBA ==============

TEST_PROFILES = [
    # E-2 Profiles (5)
    {
        "id": 1,
        "name": "Carlos Mendoza",
        "type": "E-2",
        "nationality": "Colombia",
        "profession": "Empresario",
        "experience": "15 años",
        "english": "Intermedio",
        "family": "Casado, 2 hijos",
        "budget": "$150,000",
        "motivation": "Montar negocio de mantenimiento",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "negocio",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 2,
        "name": "María García",
        "type": "E-2",
        "nationality": "México",
        "profession": "Restaurantera",
        "experience": "12 años",
        "english": "Básico",
        "family": "Casada, 1 hijo",
        "budget": "$200,000",
        "motivation": "Abrir restaurante mexicano",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "negocio",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 3,
        "name": "Roberto Sánchez",
        "type": "E-2",
        "nationality": "Argentina",
        "profession": "Consultor IT",
        "experience": "10 años",
        "english": "Avanzado",
        "family": "Soltero",
        "budget": "$120,000",
        "motivation": "Empresa de desarrollo de software",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "negocio",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 4,
        "name": "Ana Rodríguez",
        "type": "E-2",
        "nationality": "Venezuela",
        "profession": "Estilista",
        "experience": "8 años",
        "english": "Intermedio",
        "family": "Casada, sin hijos",
        "budget": "$80,000",
        "motivation": "Salón de belleza",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "negocio",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 5,
        "name": "Pedro Martínez",
        "type": "E-2",
        "nationality": "Chile",
        "profession": "Ingeniero Civil",
        "experience": "20 años",
        "english": "Avanzado",
        "family": "Casado, 3 hijos",
        "budget": "$250,000",
        "motivation": "Empresa de construcción",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "negocio",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    # L-1 Profiles (5)
    {
        "id": 6,
        "name": "Luis Fernández",
        "type": "L-1",
        "nationality": "España",
        "profession": "Director de Operaciones",
        "experience": "15 años",
        "english": "Avanzado",
        "family": "Casado, 2 hijos",
        "budget": "$100,000",
        "motivation": "Transferencia a oficina USA",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 7,
        "name": "Carmen López",
        "type": "L-1",
        "nationality": "Colombia",
        "profession": "Gerente de Marketing",
        "experience": "12 años",
        "english": "Avanzado",
        "family": "Soltera",
        "budget": "$80,000",
        "motivation": "Abrir oficina regional",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 8,
        "name": "Jorge Ramírez",
        "type": "L-1",
        "nationality": "Perú",
        "profession": "CTO",
        "experience": "18 años",
        "english": "Nativo",
        "family": "Casado, 1 hijo",
        "budget": "$150,000",
        "motivation": "Expandir startup a USA",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 9,
        "name": "Patricia Gómez",
        "type": "L-1",
        "nationality": "México",
        "profession": "Directora Financiera",
        "experience": "14 años",
        "english": "Avanzado",
        "family": "Casada, sin hijos",
        "budget": "$120,000",
        "motivation": "Fusión con empresa americana",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 10,
        "name": "Miguel Torres",
        "type": "L-1",
        "nationality": "Brasil",
        "profession": "VP de Ventas",
        "experience": "16 años",
        "english": "Avanzado",
        "family": "Casado, 2 hijos",
        "budget": "$180,000",
        "motivation": "Liderar operación norteamericana",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    # EB-2 NIW Profiles (5)
    {
        "id": 11,
        "name": "Dr. Alejandro Ruiz",
        "type": "EB-2_NIW",
        "nationality": "Colombia",
        "profession": "Investigador en IA",
        "experience": "10 años",
        "english": "Avanzado",
        "family": "Casado, 1 hijo",
        "budget": "$50,000",
        "motivation": "Continuar investigación en USA",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 12,
        "name": "Dra. Isabella Moreno",
        "type": "EB-2_NIW",
        "nationality": "Argentina",
        "profession": "Científica de Datos",
        "experience": "8 años",
        "english": "Avanzado",
        "family": "Soltera",
        "budget": "$40,000",
        "motivation": "Trabajar en Big Tech",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 13,
        "name": "Dr. Fernando Castro",
        "type": "EB-2_NIW",
        "nationality": "Chile",
        "profession": "Médico Especialista",
        "experience": "15 años",
        "english": "Intermedio",
        "family": "Casado, 3 hijos",
        "budget": "$100,000",
        "motivation": "Ejercer medicina en USA",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 14,
        "name": "Dra. Valentina Herrera",
        "type": "EB-2_NIW",
        "nationality": "Venezuela",
        "profession": "Ingeniera Biomédica",
        "experience": "12 años",
        "english": "Avanzado",
        "family": "Casada, sin hijos",
        "budget": "$60,000",
        "motivation": "Desarrollar dispositivos médicos",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 15,
        "name": "Dr. Ricardo Vargas",
        "type": "EB-2_NIW",
        "nationality": "Perú",
        "profession": "Profesor Universitario",
        "experience": "20 años",
        "english": "Avanzado",
        "family": "Casado, 2 hijos",
        "budget": "$70,000",
        "motivation": "Posición académica en USA",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    # Mixed Profiles (5)
    {
        "id": 16,
        "name": "Sofía Delgado",
        "type": "MIXED",
        "nationality": "Colombia",
        "profession": "Abogada Corporativa",
        "experience": "10 años",
        "english": "Avanzado",
        "family": "Soltera",
        "budget": "$100,000",
        "motivation": "Explorar opciones de migración",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 17,
        "name": "Diego Navarro",
        "type": "MIXED",
        "nationality": "México",
        "profession": "Arquitecto",
        "experience": "12 años",
        "english": "Intermedio",
        "family": "Casado, 1 hijo",
        "budget": "$150,000",
        "motivation": "Mejor calidad de vida",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 18,
        "name": "Lucía Reyes",
        "type": "MIXED",
        "nationality": "Ecuador",
        "profession": "Contadora",
        "experience": "8 años",
        "english": "Básico",
        "family": "Casada, 2 hijos",
        "budget": "$80,000",
        "motivation": "Futuro para los hijos",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
    {
        "id": 19,
        "name": "Andrés Molina",
        "type": "MIXED",
        "nationality": "Costa Rica",
        "profession": "Diseñador UX",
        "experience": "6 años",
        "english": "Avanzado",
        "family": "Soltero",
        "budget": "$60,000",
        "motivation": "Trabajar en Silicon Valley",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "plan",
        ],
    },
    {
        "id": 20,
        "name": "Gabriela Ortiz",
        "type": "MIXED",
        "nationality": "Panamá",
        "profession": "Gerente de Proyectos",
        "experience": "14 años",
        "english": "Avanzado",
        "family": "Casada, 1 hijo",
        "budget": "$120,000",
        "motivation": "Oportunidades profesionales",
        "expected_flow": [
            "registro",
            "diagnostico",
            "perfilamiento",
            "visa",
            "estado",
            "ciudad",
            "barrio",
            "vivienda",
            "colegios",
            "plan",
        ],
    },
]


# ============== SIMULADOR ==============


@dataclass
class FrictionEvent:
    """Evento de fricción detectado"""

    profile_id: int
    turn: int
    phase: str
    type: str
    description: str
    severity: str  # low, medium, high, critical


@dataclass
class SimulationResult:
    """Resultado de una simulación"""

    profile_id: int
    profile_name: str
    profile_type: str
    total_turns: int
    phases_completed: list[str]
    frictions: list[FrictionEvent]
    rules_violated: list[str]
    micro_checks_used: int
    forms_shown: int
    gating_respected: bool
    matrix_evaluations: int
    success: bool
    notes: str


class E2ESimulator:
    """Simulador E2E de conversaciones MigPAL"""

    def __init__(self):
        self.standard = get_migpal_standard()
        self.results: list[SimulationResult] = []
        self.all_frictions: list[FrictionEvent] = []

    def simulate_conversation(self, profile: dict[str, Any]) -> SimulationResult:
        """Simula una conversación completa para un perfil"""

        user_id = profile["id"] + 10000  # Offset para IDs de prueba
        frictions = []
        rules_violated = []
        phases_completed = []
        micro_checks = 0
        forms_shown = 0
        matrix_evals = 0
        gating_ok = True

        # Resetear estado
        self.standard._states.pop(user_id, None)
        state = self.standard.get_state(user_id)

        turn = 0
        max_turns = 100  # Límite de seguridad

        # Simular flujo esperado
        for expected_phase in profile["expected_flow"]:
            turn += 1
            if turn > max_turns:
                frictions.append(
                    FrictionEvent(
                        profile_id=profile["id"],
                        turn=turn,
                        phase=expected_phase,
                        type="infinite_loop",
                        description="Conversación excedió límite de turnos",
                        severity="critical",
                    )
                )
                break

            # Simular mensaje del usuario
            user_message = self._generate_user_message(profile, expected_phase, turn)

            # Procesar con el estándar
            response = self.standard.format_response(user_id, f"Respuesta para: {user_message}")

            # Verificar reglas
            violations = self._check_rules(response, state, turn)
            rules_violated.extend(violations)

            # Verificar micro-checks
            if response.include_micro_check:
                micro_checks += 1

            # Verificar formularios
            if response.is_form:
                forms_shown += 1
                if not self.standard.can_show_form(user_id):
                    frictions.append(
                        FrictionEvent(
                            profile_id=profile["id"],
                            turn=turn,
                            phase=expected_phase,
                            type="form_overflow",
                            description="Formulario mostrado cuando no debía",
                            severity="medium",
                        )
                    )

            # Verificar gating en fase de visa
            if expected_phase == "visa":
                can_recommend, msg = check_visa_gating(user_id)
                if can_recommend and not state.profile_complete:
                    gating_ok = False
                    frictions.append(
                        FrictionEvent(
                            profile_id=profile["id"],
                            turn=turn,
                            phase=expected_phase,
                            type="gating_violation",
                            description="Recomendación de visa sin perfil completo",
                            severity="critical",
                        )
                    )

            # Simular evaluaciones con matriz
            if expected_phase in ["estado", "ciudad", "negocio", "barrio", "colegios"]:
                matrix_evals += 1

            phases_completed.append(expected_phase)

        # Marcar perfil como completo después de perfilamiento
        if "perfilamiento" in phases_completed:
            self.standard.update_state(user_id, profile_complete=True)

        # Marcar resumen confirmado
        if "visa" in phases_completed:
            self.standard.update_state(user_id, summary_confirmed=True)

        result = SimulationResult(
            profile_id=profile["id"],
            profile_name=profile["name"],
            profile_type=profile["type"],
            total_turns=turn,
            phases_completed=phases_completed,
            frictions=frictions,
            rules_violated=rules_violated,
            micro_checks_used=micro_checks,
            forms_shown=forms_shown,
            gating_respected=gating_ok,
            matrix_evaluations=matrix_evals,
            success=len([f for f in frictions if f.severity == "critical"]) == 0,
            notes="",
        )

        self.results.append(result)
        self.all_frictions.extend(frictions)

        return result

    def _generate_user_message(self, profile: dict, phase: str, turn: int) -> str:
        """Genera mensaje simulado del usuario"""
        messages = {
            "registro": f"Hola, soy {profile['name']} de {profile['nationality']}",
            "diagnostico": f"Soy {profile['profession']} con {profile['experience']} de experiencia",
            "perfilamiento": f"Mi familia: {profile['family']}. Presupuesto: {profile['budget']}",
            "visa": f"Mi motivación es: {profile['motivation']}",
            "estado": "Quiero evaluar estados para vivir",
            "ciudad": "Me gustaría ver opciones de ciudades",
            "negocio": "Necesito ayuda para elegir tipo de negocio",
            "barrio": "¿Qué barrios me recomiendas?",
            "vivienda": "Busco opciones de vivienda",
            "colegios": "Necesito información de colegios para mis hijos",
            "plan": "Estoy listo para ver el plan completo",
        }
        return messages.get(phase, "Continúa por favor")

    def _check_rules(self, response, state, turn: int) -> list[str]:
        """Verifica cumplimiento de reglas"""
        violations = []

        # Verificar longitud del mensaje
        lines = response.text.split("\n")
        if len(lines) > 8:  # Permitir un poco más por formato
            violations.append(f"Turn {turn}: Mensaje muy largo ({len(lines)} líneas)")

        # Verificar frases prohibidas
        text_lower = response.text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text_lower:
                violations.append(f"Turn {turn}: Frase prohibida detectada: '{phrase}'")

        # Verificar múltiples preguntas
        questions = response.text.count("?")
        if questions > 2:  # Permitir micro-check + pregunta principal
            violations.append(f"Turn {turn}: Múltiples preguntas ({questions})")

        return violations

    def run_all_simulations(self) -> dict[str, Any]:
        """Ejecuta todas las simulaciones"""
        print("=" * 60)
        print("🚀 INICIANDO SIMULACIÓN E2E - 20 CONVERSACIONES")
        print("=" * 60)

        for i, profile in enumerate(TEST_PROFILES, 1):
            print(f"\n[{i}/20] Simulando: {profile['name']} ({profile['type']})")
            result = self.simulate_conversation(profile)
            status = "✅" if result.success else "❌"
            print(f"  {status} Turnos: {result.total_turns}, Fricciones: {len(result.frictions)}")

        return self.generate_report()

    def generate_report(self) -> dict[str, Any]:
        """Genera reporte de resultados"""

        total = len(self.results)
        successful = len([r for r in self.results if r.success])
        failed = total - successful

        # Agrupar fricciones por tipo
        friction_by_type = {}
        for f in self.all_frictions:
            if f.type not in friction_by_type:
                friction_by_type[f.type] = []
            friction_by_type[f.type].append(f)

        # Agrupar fricciones por severidad
        friction_by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for f in self.all_frictions:
            friction_by_severity[f.severity].append(f)

        # Calcular métricas
        avg_turns = sum(r.total_turns for r in self.results) / total if total > 0 else 0
        avg_micro_checks = sum(r.micro_checks_used for r in self.results) / total if total > 0 else 0
        avg_forms = sum(r.forms_shown for r in self.results) / total if total > 0 else 0
        gating_compliance = (
            len([r for r in self.results if r.gating_respected]) / total * 100 if total > 0 else 0
        )

        # Todas las violaciones de reglas
        all_violations = []
        for r in self.results:
            all_violations.extend(r.rules_violated)

        report = {
            "summary": {
                "total_simulations": total,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total)*100:.1f}%" if total > 0 else "N/A",
                "total_frictions": len(self.all_frictions),
                "critical_frictions": len(friction_by_severity["critical"]),
            },
            "metrics": {
                "avg_turns_per_conversation": round(avg_turns, 1),
                "avg_micro_checks": round(avg_micro_checks, 1),
                "avg_forms_shown": round(avg_forms, 1),
                "gating_compliance": f"{gating_compliance:.1f}%",
            },
            "frictions_by_type": {k: len(v) for k, v in friction_by_type.items()},
            "frictions_by_severity": {k: len(v) for k, v in friction_by_severity.items()},
            "rule_violations": all_violations[:20],  # Top 20
            "recommendations": self._generate_recommendations(friction_by_type, all_violations),
            "detailed_results": [
                {
                    "profile": r.profile_name,
                    "type": r.profile_type,
                    "success": r.success,
                    "turns": r.total_turns,
                    "frictions": len(r.frictions),
                    "phases": r.phases_completed,
                }
                for r in self.results
            ],
        }

        return report

    def _generate_recommendations(self, friction_by_type: dict, violations: list) -> list[str]:
        """Genera recomendaciones basadas en fricciones"""
        recommendations = []

        if "gating_violation" in friction_by_type:
            recommendations.append("🔴 CRÍTICO: Reforzar gating de visa - no recomendar sin perfil completo")

        if "form_overflow" in friction_by_type:
            recommendations.append("🟡 Reducir frecuencia de formularios - máximo 1 cada 5 turnos")

        if "infinite_loop" in friction_by_type:
            recommendations.append("🔴 CRÍTICO: Revisar flujo de estados - detectados loops infinitos")

        if any("Mensaje muy largo" in v for v in violations):
            recommendations.append("🟡 Acortar mensajes - máximo 6 líneas por respuesta")

        if any("Frase prohibida" in v for v in violations):
            recommendations.append("🟡 Suavizar tono - eliminar frases sentenciosas")

        if any("Múltiples preguntas" in v for v in violations):
            recommendations.append("🟡 Una pregunta por mensaje - evitar múltiples preguntas")

        if not recommendations:
            recommendations.append("✅ No se detectaron problemas críticos")

        return recommendations


def main():
    """Función principal"""
    simulator = E2ESimulator()
    report = simulator.run_all_simulations()

    # Imprimir reporte
    print("\n" + "=" * 60)
    print("📊 REPORTE DE SIMULACIÓN E2E")
    print("=" * 60)

    print("\n📈 RESUMEN:")
    for key, value in report["summary"].items():
        print(f"  • {key}: {value}")

    print("\n📉 MÉTRICAS:")
    for key, value in report["metrics"].items():
        print(f"  • {key}: {value}")

    print("\n⚠️ FRICCIONES POR TIPO:")
    for ftype, count in report["frictions_by_type"].items():
        print(f"  • {ftype}: {count}")

    print("\n🚨 FRICCIONES POR SEVERIDAD:")
    for severity, count in report["frictions_by_severity"].items():
        emoji = (
            "🔴"
            if severity == "critical"
            else "🟠" if severity == "high" else "🟡" if severity == "medium" else "🟢"
        )
        print(f"  {emoji} {severity}: {count}")

    print("\n💡 RECOMENDACIONES:")
    for rec in report["recommendations"]:
        print(f"  {rec}")

    print("\n📋 RESULTADOS DETALLADOS:")
    for r in report["detailed_results"]:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['profile']} ({r['type']}): {r['turns']} turnos, {r['frictions']} fricciones")

    # Guardar reporte JSON
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports", "e2e_simulation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📁 Reporte guardado en: {report_path}")

    return report


if __name__ == "__main__":
    main()
