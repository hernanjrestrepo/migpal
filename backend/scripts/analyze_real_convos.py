#!/usr/bin/env python3
"""
MigPAL Real Conversation Analyzer V1.0
======================================
Analiza logs de conversaciones reales y genera:
- Lista de bugs reproducibles
- Pasos para reproducir cada bug
- Estadísticas de fricción
- Recomendaciones de mejora

Uso:
    python analyze_real_convos.py                    # Analiza todos los logs
    python analyze_real_convos.py --date 2026-01-08  # Analiza un día específico
    python analyze_real_convos.py --user 123456      # Analiza un usuario específico
"""

import argparse
import json
import logging

# Setup path
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Bug:
    """Representa un bug detectado"""

    bug_id: str
    bug_type: str
    severity: str  # critical, high, medium, low
    description: str
    user_id: int
    session_id: str
    timestamp: str
    state: str
    reproduction_steps: list[str]
    context: dict[str, Any] = field(default_factory=dict)
    occurrences: int = 1


@dataclass
class AnalysisReport:
    """Reporte de análisis"""

    analysis_date: str
    sessions_analyzed: int
    users_analyzed: int
    total_messages: int
    bugs_found: list[Bug]
    friction_stats: dict[str, int]
    state_distribution: dict[str, int]
    completion_rate: float
    avg_session_duration: float
    recommendations: list[str]


class ConversationAnalyzer:
    """Analizador de conversaciones reales"""

    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data" / "conversations"

        self.bugs: list[Bug] = []
        self.bug_counter = 0

    def load_sessions(self, date: str = None, user_id: int = None) -> list[dict]:
        """Carga sesiones de conversación"""
        sessions = []

        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return sessions

        # Determinar qué directorios buscar
        if date:
            dirs_to_search = [self.data_dir / date]
        else:
            dirs_to_search = [d for d in self.data_dir.iterdir() if d.is_dir()]

        for dir_path in dirs_to_search:
            if not dir_path.exists():
                continue

            for file_path in dir_path.glob("*.json"):
                # Filtrar por user_id si se especificó
                if user_id:
                    if not file_path.name.startswith(f"{user_id}_"):
                        continue

                try:
                    with open(file_path, encoding="utf-8") as f:
                        session = json.load(f)
                        session["_file_path"] = str(file_path)
                        sessions.append(session)
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")

        return sessions

    def _generate_bug_id(self) -> str:
        """Genera ID único para bug"""
        self.bug_counter += 1
        return f"BUG-{self.bug_counter:04d}"

    def detect_loop_bug(self, session: dict) -> Bug | None:
        """Detecta bugs de loop"""
        messages = session.get("messages", [])

        # Buscar mensajes de bot repetidos
        bot_msgs = [(i, m) for i, m in enumerate(messages) if m["sender"] == "bot"]

        for i in range(len(bot_msgs) - 2):
            idx1, msg1 = bot_msgs[i]
            idx2, msg2 = bot_msgs[i + 1]
            idx3, msg3 = bot_msgs[i + 2]

            # Normalizar para comparación
            text1 = msg1["text"].lower().strip()
            text2 = msg2["text"].lower().strip()
            text3 = msg3["text"].lower().strip()

            if text1 == text2 == text3:
                # Encontrar mensajes de usuario entre los loops
                user_msgs = [m for m in messages[idx1 : idx3 + 1] if m["sender"] == "user"]

                return Bug(
                    bug_id=self._generate_bug_id(),
                    bug_type="LOOP",
                    severity="critical",
                    description=f"Bot repeated same message 3+ times: '{msg1['text'][:50]}...'",
                    user_id=session["user_id"],
                    session_id=session["session_id"],
                    timestamp=msg1["timestamp"],
                    state=msg1.get("state", "unknown"),
                    reproduction_steps=[
                        f"1. Navigate to state: {msg1.get('state', 'unknown')}",
                        f"2. Send message: '{user_msgs[0]['text'] if user_msgs else 'N/A'}'",
                        "3. Observe bot response repeating",
                        f"4. Send another message: '{user_msgs[1]['text'] if len(user_msgs) > 1 else 'N/A'}'",
                        "5. Bot repeats same response again",
                    ],
                    context={"repeated_message": msg1["text"], "user_inputs": [m["text"] for m in user_msgs]},
                )

        return None

    def detect_phantom_data_bug(self, session: dict) -> Bug | None:
        """Detecta bugs de datos fantasma"""
        messages = session.get("messages", [])

        for msg in messages:
            if msg["sender"] != "user":
                continue

            friction_tags = msg.get("friction_tags", [])
            if "phantom_data" in friction_tags:
                extracted = msg.get("extracted_fields", {})

                return Bug(
                    bug_id=self._generate_bug_id(),
                    bug_type="PHANTOM_DATA",
                    severity="critical",
                    description=f"Phantom data saved: {extracted}",
                    user_id=session["user_id"],
                    session_id=session["session_id"],
                    timestamp=msg["timestamp"],
                    state=msg.get("state", "unknown"),
                    reproduction_steps=[
                        f"1. Navigate to state: {msg.get('state', 'unknown')}",
                        f"2. Send message: '{msg['text']}'",
                        f"3. Observe that invalid data was saved: {extracted}",
                    ],
                    context={"user_input": msg["text"], "extracted_fields": extracted},
                )

        return None

    def detect_confusion_bug(self, session: dict) -> Bug | None:
        """Detecta bugs donde el usuario quedó confundido"""
        messages = session.get("messages", [])

        confusion_count = 0
        confusion_msgs = []

        for msg in messages:
            if msg["sender"] != "user":
                continue

            friction_tags = msg.get("friction_tags", [])
            if "confusion" in friction_tags:
                confusion_count += 1
                confusion_msgs.append(msg)

                if confusion_count >= 3:
                    return Bug(
                        bug_id=self._generate_bug_id(),
                        bug_type="USER_CONFUSION",
                        severity="high",
                        description=f"User expressed confusion {confusion_count} times",
                        user_id=session["user_id"],
                        session_id=session["session_id"],
                        timestamp=confusion_msgs[0]["timestamp"],
                        state=confusion_msgs[0].get("state", "unknown"),
                        reproduction_steps=[
                            f"1. Navigate to state: {confusion_msgs[0].get('state', 'unknown')}",
                            "2. User messages indicating confusion:",
                            *[f"   - '{m['text']}'" for m in confusion_msgs[:3]],
                        ],
                        context={
                            "confusion_messages": [m["text"] for m in confusion_msgs],
                            "states": [m.get("state", "unknown") for m in confusion_msgs],
                        },
                    )

        return None

    def detect_rage_quit(self, session: dict) -> Bug | None:
        """Detecta abandonos por frustración"""
        messages = session.get("messages", [])

        if not messages:
            return None

        # Buscar rage tags seguidos de abandono
        for i, msg in enumerate(messages):
            if msg["sender"] != "user":
                continue

            friction_tags = msg.get("friction_tags", [])
            if "rage" in friction_tags:
                # Verificar si es el último mensaje o cerca del final
                remaining = len(messages) - i - 1
                if remaining <= 2:
                    return Bug(
                        bug_id=self._generate_bug_id(),
                        bug_type="RAGE_QUIT",
                        severity="high",
                        description="User abandoned after expressing frustration",
                        user_id=session["user_id"],
                        session_id=session["session_id"],
                        timestamp=msg["timestamp"],
                        state=msg.get("state", "unknown"),
                        reproduction_steps=[
                            f"1. Navigate to state: {msg.get('state', 'unknown')}",
                            f"2. User expressed frustration: '{msg['text']}'",
                            "3. User abandoned conversation shortly after",
                        ],
                        context={
                            "frustration_message": msg["text"],
                            "state_at_abandon": msg.get("state", "unknown"),
                        },
                    )

        return None

    def detect_stuck_state(self, session: dict) -> Bug | None:
        """Detecta estados donde el usuario quedó atascado"""
        messages = session.get("messages", [])

        if len(messages) < 6:
            return None

        # Contar mensajes por estado
        state_counts = defaultdict(list)
        for msg in messages:
            state = msg.get("state", "unknown")
            state_counts[state].append(msg)

        # Buscar estados con muchos mensajes
        for state, msgs in state_counts.items():
            if len(msgs) >= 6:
                user_msgs = [m for m in msgs if m["sender"] == "user"]
                if len(user_msgs) >= 3:
                    return Bug(
                        bug_id=self._generate_bug_id(),
                        bug_type="STATE_STUCK",
                        severity="medium",
                        description=f"User stuck in state '{state}' for {len(msgs)} messages",
                        user_id=session["user_id"],
                        session_id=session["session_id"],
                        timestamp=msgs[0]["timestamp"],
                        state=state,
                        reproduction_steps=[
                            f"1. Navigate to state: {state}",
                            "2. User attempts:",
                            *[f"   - '{m['text']}'" for m in user_msgs[:3]],
                            "3. User remains stuck in same state",
                        ],
                        context={
                            "state": state,
                            "message_count": len(msgs),
                            "user_attempts": [m["text"] for m in user_msgs],
                        },
                    )

        return None

    def analyze_session(self, session: dict) -> list[Bug]:
        """Analiza una sesión y detecta bugs"""
        bugs = []

        # Detectar diferentes tipos de bugs
        detectors = [
            self.detect_loop_bug,
            self.detect_phantom_data_bug,
            self.detect_confusion_bug,
            self.detect_rage_quit,
            self.detect_stuck_state,
        ]

        for detector in detectors:
            bug = detector(session)
            if bug:
                bugs.append(bug)

        return bugs

    def analyze_all(self, date: str = None, user_id: int = None) -> AnalysisReport:
        """Analiza todas las sesiones y genera reporte"""
        sessions = self.load_sessions(date=date, user_id=user_id)

        if not sessions:
            logger.warning("No sessions found to analyze")
            return AnalysisReport(
                analysis_date=datetime.now().isoformat(),
                sessions_analyzed=0,
                users_analyzed=0,
                total_messages=0,
                bugs_found=[],
                friction_stats={},
                state_distribution={},
                completion_rate=0,
                avg_session_duration=0,
                recommendations=["No data to analyze"],
            )

        # Analizar cada sesión
        all_bugs = []
        friction_stats = defaultdict(int)
        state_distribution = defaultdict(int)
        total_messages = 0
        completed_sessions = 0
        total_duration = 0
        unique_users = set()

        for session in sessions:
            # Detectar bugs
            bugs = self.analyze_session(session)
            all_bugs.extend(bugs)

            # Estadísticas
            unique_users.add(session["user_id"])
            total_messages += session.get("total_messages", 0)

            if session.get("completed"):
                completed_sessions += 1

            total_duration += session.get("duration_seconds", 0)

            # Fricción
            for tag, count in session.get("friction_summary", {}).items():
                friction_stats[tag] += count

            # Estados
            for state in session.get("states_visited", []):
                state_distribution[state] += 1

        # Calcular métricas
        completion_rate = completed_sessions / len(sessions) if sessions else 0
        avg_duration = total_duration / len(sessions) if sessions else 0

        # Generar recomendaciones
        recommendations = self._generate_recommendations(all_bugs, friction_stats)

        # Deduplicar bugs similares
        deduplicated_bugs = self._deduplicate_bugs(all_bugs)

        return AnalysisReport(
            analysis_date=datetime.now().isoformat(),
            sessions_analyzed=len(sessions),
            users_analyzed=len(unique_users),
            total_messages=total_messages,
            bugs_found=deduplicated_bugs,
            friction_stats=dict(friction_stats),
            state_distribution=dict(state_distribution),
            completion_rate=completion_rate,
            avg_session_duration=avg_duration,
            recommendations=recommendations,
        )

    def _deduplicate_bugs(self, bugs: list[Bug]) -> list[Bug]:
        """Agrupa bugs similares"""
        bug_groups = defaultdict(list)

        for bug in bugs:
            key = (bug.bug_type, bug.state, bug.description[:50])
            bug_groups[key].append(bug)

        deduplicated = []
        for key, group in bug_groups.items():
            representative = group[0]
            representative.occurrences = len(group)
            deduplicated.append(representative)

        return deduplicated

    def _generate_recommendations(self, bugs: list[Bug], friction_stats: dict[str, int]) -> list[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []

        # Basado en bugs
        bug_types = defaultdict(int)
        for bug in bugs:
            bug_types[bug.bug_type] += 1

        if bug_types.get("LOOP", 0) > 0:
            recommendations.append(
                f"🔴 CRITICAL: {bug_types['LOOP']} loop bugs detected. "
                "Review bot response logic to prevent repetition."
            )

        if bug_types.get("PHANTOM_DATA", 0) > 0:
            recommendations.append(
                f"🔴 CRITICAL: {bug_types['PHANTOM_DATA']} phantom data bugs. "
                "Strengthen NameValidator and data extraction rules."
            )

        if bug_types.get("USER_CONFUSION", 0) > 0:
            recommendations.append(
                f"🟡 HIGH: {bug_types['USER_CONFUSION']} user confusion incidents. "
                "Improve clarity of bot messages and add more examples."
            )

        if bug_types.get("RAGE_QUIT", 0) > 0:
            recommendations.append(
                f"🟡 HIGH: {bug_types['RAGE_QUIT']} rage quit incidents. "
                "Review UX flow and add escape hatches for frustrated users."
            )

        if bug_types.get("STATE_STUCK", 0) > 0:
            recommendations.append(
                f"🟠 MEDIUM: {bug_types['STATE_STUCK']} state stuck incidents. "
                "Add timeout handlers and alternative paths."
            )

        # Basado en fricción
        if friction_stats.get("loop", 0) > 5:
            recommendations.append(
                f"⚠️ High loop friction ({friction_stats['loop']} occurrences). "
                "Implement response rotation."
            )

        if friction_stats.get("confusion", 0) > 10:
            recommendations.append(
                f"⚠️ High confusion friction ({friction_stats['confusion']} occurrences). "
                "Add clarification prompts."
            )

        if not recommendations:
            recommendations.append("✅ No critical issues detected.")

        return recommendations


def generate_report_md(report: AnalysisReport) -> str:
    """Genera reporte en formato Markdown"""
    md = f"""# Conversation Analysis Report

**Analysis Date:** {report.analysis_date}
**Sessions Analyzed:** {report.sessions_analyzed}
**Unique Users:** {report.users_analyzed}
**Total Messages:** {report.total_messages}
**Completion Rate:** {report.completion_rate*100:.1f}%
**Avg Session Duration:** {report.avg_session_duration:.1f}s

---

## Summary

| Metric | Value |
|--------|-------|
| Total Bugs | {len(report.bugs_found)} |
| Critical | {sum(1 for b in report.bugs_found if b.severity == 'critical')} |
| High | {sum(1 for b in report.bugs_found if b.severity == 'high')} |
| Medium | {sum(1 for b in report.bugs_found if b.severity == 'medium')} |
| Low | {sum(1 for b in report.bugs_found if b.severity == 'low')} |

## Friction Statistics

"""

    if report.friction_stats:
        for tag, count in sorted(report.friction_stats.items(), key=lambda x: -x[1]):
            md += f"- **{tag}:** {count}\n"
    else:
        md += "- No friction detected\n"

    md += "\n## Recommendations\n\n"

    for rec in report.recommendations:
        md += f"- {rec}\n"

    md += "\n---\n\n## Bugs Found\n\n"

    if report.bugs_found:
        for bug in sorted(
            report.bugs_found, key=lambda b: {"critical": 0, "high": 1, "medium": 2, "low": 3}[b.severity]
        ):
            severity_icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}[bug.severity]

            md += f"""### {severity_icon} {bug.bug_id}: {bug.bug_type}

**Severity:** {bug.severity.upper()}
**Occurrences:** {bug.occurrences}
**User:** {bug.user_id}
**State:** {bug.state}
**Timestamp:** {bug.timestamp}

**Description:** {bug.description}

**Reproduction Steps:**
"""
            for step in bug.reproduction_steps:
                md += f"{step}\n"

            md += "\n---\n\n"
    else:
        md += "No bugs detected.\n"

    md += """
---
*Generated by analyze_real_convos.py*
"""

    return md


def main():
    parser = argparse.ArgumentParser(description="Analyze real conversation logs")
    parser.add_argument("--date", type=str, help="Analyze specific date (YYYY-MM-DD)")
    parser.add_argument("--user", type=int, help="Analyze specific user ID")
    parser.add_argument("--output", type=str, help="Output directory")

    args = parser.parse_args()

    print("=" * 60)
    print("MigPAL Conversation Analyzer")
    print("=" * 60)

    analyzer = ConversationAnalyzer()
    report = analyzer.analyze_all(date=args.date, user_id=args.user)

    # Generar reporte MD
    md_content = generate_report_md(report)

    # Determinar directorio de salida
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Guardar archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.date:
        filename_base = f"analysis_{args.date}"
    elif args.user:
        filename_base = f"analysis_user_{args.user}"
    else:
        filename_base = f"analysis_{timestamp}"

    md_path = output_dir / f"{filename_base}.md"
    json_path = output_dir / f"{filename_base}.json"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Convertir bugs a dict para JSON
    report_dict = {
        "analysis_date": report.analysis_date,
        "sessions_analyzed": report.sessions_analyzed,
        "users_analyzed": report.users_analyzed,
        "total_messages": report.total_messages,
        "completion_rate": report.completion_rate,
        "avg_session_duration": report.avg_session_duration,
        "friction_stats": report.friction_stats,
        "state_distribution": report.state_distribution,
        "recommendations": report.recommendations,
        "bugs_found": [
            {
                "bug_id": b.bug_id,
                "bug_type": b.bug_type,
                "severity": b.severity,
                "description": b.description,
                "user_id": b.user_id,
                "session_id": b.session_id,
                "timestamp": b.timestamp,
                "state": b.state,
                "reproduction_steps": b.reproduction_steps,
                "context": b.context,
                "occurrences": b.occurrences,
            }
            for b in report.bugs_found
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    # Imprimir resumen
    print("\n📊 Analysis Complete")
    print(f"   Sessions: {report.sessions_analyzed}")
    print(f"   Users: {report.users_analyzed}")
    print(f"   Bugs Found: {len(report.bugs_found)}")
    print(f"   Completion Rate: {report.completion_rate*100:.1f}%")

    print("\n📄 Reports saved to:")
    print(f"   MD: {md_path}")
    print(f"   JSON: {json_path}")

    if report.bugs_found:
        print("\n🐛 Bugs by Severity:")
        for severity in ["critical", "high", "medium", "low"]:
            count = sum(1 for b in report.bugs_found if b.severity == severity)
            if count > 0:
                icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}[severity]
                print(f"   {icon} {severity.upper()}: {count}")


if __name__ == "__main__":
    main()
