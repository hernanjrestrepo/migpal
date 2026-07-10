#!/usr/bin/env python3
"""
E2E CLIENT SIMULATION - Full Flow Test V4.2.1
==============================================
Simula un cliente REAL (no tester) recorriendo el flujo completo:
/start → saludo → emoción → perfilamiento → avance de fase

V4.2.1 FIX D: Validaciones adicionales:
- Detectar respuestas solo-emoji (placeholder sin contenido)
- Detectar regresión de estado (state retrocede)

Ejecutar: python scripts/e2e_client_simulation.py
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simulation config
TEST_USER_ID = 888888888
SIMULATION_NAME = "María García"

# Conversation flow - natural client messages
CLIENT_MESSAGES = [
    {"type": "command", "text": "/start", "description": "Inicio de conversación"},
    {"type": "message", "text": "Hola", "description": "Saludo inicial"},
    {"type": "message", "text": "Confundido", "description": "Expresión de confusión"},
    {"type": "message", "text": "No sé por dónde comenzar", "description": "Necesita orientación"},
    {"type": "message", "text": "Soy ingeniera de software", "description": "Respuesta a profesión"},
    {"type": "message", "text": "Tengo 5 años de experiencia", "description": "Experiencia laboral"},
    {"type": "message", "text": "Quiero ir a Estados Unidos", "description": "Destino deseado"},
    {
        "type": "message",
        "text": "Mi presupuesto es de unos 15000 dólares",
        "description": "Información financiera",
    },
]

# Forbidden patterns
FORBIDDEN_PATTERNS = [
    "⚠️",
    "⏳ Sigo aquí",
    "Traceback",
    "AttributeError",
    "KeyError",
    "TypeError",
    "Exception",
    "'NoneType'",
    "error:",
    "ERROR",
]

# V4.2.1 FIX D: Estados que NO deben retroceder
STATE_PROGRESSION = {
    "onboarding_question": 1,
    "onboarding_explain": 2,
    "onboarding_consent": 3,
    "emotion_clarification": 4,
    "name": 5,
    "confirm_name": 6,
    "birth_date": 7,
    "nationality": 8,
    "current_country": 9,
    "start": 0,
}

# Results storage
RESULTS = {
    "simulation_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
    "user_id": TEST_USER_ID,
    "user_name": SIMULATION_NAME,
    "start_time": None,
    "end_time": None,
    "transcript": [],
    "diagnostics": {
        "frictions": [],
        "engagement_score": 0,
        "clarity_score": 0,
        "empathy_score": 0,
        "errors": [],
        "duplicates": [],
        "loops_detected": False,
        "forbidden_patterns_found": [],
        "emoji_only_responses": [],
        "state_regressions": [],
    },
    "states_visited": [],
    "verdict": "PENDING",
    "actions_needed": [],
}


def log(msg: str, level: str = "INFO"):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    icon = {"INFO": "🔹", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "•")
    print(f"{icon} [{timestamp}] {msg}")


def add_transcript(turn: int, role: str, message: str, state: str = "", metadata: dict = None):
    """Add entry to transcript"""
    entry = {
        "turn": turn,
        "role": role,
        "message": message[:500] if message else "",
        "state": state,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
    }
    RESULTS["transcript"].append(entry)

    role_icon = "👤" if role == "USER" else "🤖"
    msg_preview = message[:100].replace("\n", " ") if message else "(empty)"
    print(f"   {role_icon} [{role}] {msg_preview}{'...' if len(message or '') > 100 else ''}")


def check_forbidden_patterns(text: str) -> list:
    """Check for forbidden patterns in text"""
    found = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            found.append(pattern)
    return found


def is_emoji_only_response(text: str) -> bool:
    """V4.2.1 FIX D: Check if response is only emojis/placeholders without real content"""
    if not text:
        return True

    cleaned = text.strip()

    # Check for airplane animation pattern
    if re.match(r"^[🌍🇦-🇿✈️·\s]+$", cleaned):
        return True

    # Check if response has actual text content (letters)
    has_letters = bool(re.search(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]", cleaned))
    return not has_letters


def check_state_regression(prev_state: str, new_state: str, turn: int) -> bool:
    """V4.2.1 FIX D: Check if state regressed (went backwards in flow)"""
    prev_level = STATE_PROGRESSION.get(prev_state, 0)
    new_level = STATE_PROGRESSION.get(new_state, 0)

    # Special case: start can be initial state
    if turn <= 2 and new_state == "start":
        return False

    # Going from emotion_clarification to start is a regression
    if prev_state == "emotion_clarification" and new_state == "start":
        return True

    # Regression if new level is lower than previous
    if new_level < prev_level and prev_state != "emotion_clarification":
        return True

    return False


def analyze_response(response: str, turn: int) -> dict:
    """Analyze bot response for quality metrics"""
    analysis = {
        "length": len(response) if response else 0,
        "has_emoji": any(c in response for c in "👋🌟💭✅❌⚠️🎯📍") if response else False,
        "has_question": "?" in response if response else False,
        "empathy_words": 0,
        "clarity_score": 0,
    }

    if response:
        empathy_words = [
            "entiendo",
            "comprendo",
            "tranquilo",
            "normal",
            "ayudo",
            "aquí",
            "juntos",
            "paso a paso",
        ]
        analysis["empathy_words"] = sum(1 for w in empathy_words if w.lower() in response.lower())

        if len(response) > 50 and len(response) < 500:
            analysis["clarity_score"] = 8
        elif len(response) >= 500:
            analysis["clarity_score"] = 5
        else:
            analysis["clarity_score"] = 6

        if analysis["has_question"]:
            analysis["clarity_score"] += 1

    return analysis


async def run_simulation():
    """Run the full E2E simulation"""

    print("\n" + "=" * 70)
    print("🎭 E2E CLIENT SIMULATION - Full Flow Test V4.2.1")
    print("=" * 70)
    print(f"📋 Simulation ID: {RESULTS['simulation_id']}")
    print(f"👤 Client: {SIMULATION_NAME} (ID: {TEST_USER_ID})")
    print("=" * 70 + "\n")

    RESULTS["start_time"] = datetime.now().isoformat()

    log("Importing bot modules...")
    try:
        from app.services import telegram_bot as tb

        log("Modules imported successfully", "PASS")
    except Exception as e:
        log(f"Import failed: {e}", "FAIL")
        RESULTS["diagnostics"]["errors"].append(f"Import error: {e}")
        RESULTS["verdict"] = "NO-GO"
        return False

    log("Creating bot instance...")
    try:
        bot = tb.MigPALBot()
        log("Bot instance created", "PASS")
    except Exception as e:
        log(f"Bot creation failed: {e}", "FAIL")
        RESULTS["diagnostics"]["errors"].append(f"Bot creation error: {e}")
        RESULTS["verdict"] = "NO-GO"
        return False

    # Clean up any existing state
    if TEST_USER_ID in tb.user_data:
        del tb.user_data[TEST_USER_ID]

    captured_responses = []
    captured_buttons = []

    def create_mock_update(text: str = None, is_command: bool = False):
        mock_update = MagicMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = TEST_USER_ID
        mock_update.effective_user.first_name = SIMULATION_NAME.split()[0]
        mock_update.effective_user.language_code = "es"

        mock_update.message = MagicMock()
        mock_update.message.text = text
        mock_update.message.from_user = mock_update.effective_user

        async def capture_reply(msg, **kwargs):
            captured_responses.append(msg)
            if "reply_markup" in kwargs and kwargs["reply_markup"]:
                captured_buttons.append(kwargs["reply_markup"])
            return MagicMock()

        mock_update.message.reply_text = AsyncMock(side_effect=capture_reply)
        mock_update.callback_query = None

        return mock_update

    mock_context = MagicMock()
    mock_context.bot = MagicMock()
    mock_context.bot.send_message = AsyncMock()

    print("\n" + "-" * 70)
    print("📝 CONVERSATION TRANSCRIPT")
    print("-" * 70 + "\n")

    turn = 0
    all_passed = True
    previous_responses = []
    previous_state = "start"

    for msg_config in CLIENT_MESSAGES:
        turn += 1
        msg_text = msg_config["text"]
        msg_type = msg_config["type"]
        msg_desc = msg_config["description"]

        print(f"\n--- Turn {turn}: {msg_desc} ---")

        try:
            current_state = tb.get_state(TEST_USER_ID)
        except:
            current_state = "start"

        add_transcript(turn, "USER", msg_text, current_state, {"description": msg_desc})

        captured_responses.clear()
        captured_buttons.clear()

        try:
            update = create_mock_update(msg_text, is_command=(msg_type == "command"))

            try:
                if msg_type == "command" and msg_text == "/start":
                    await asyncio.wait_for(bot._cmd_start(update, mock_context), timeout=30.0)
                else:
                    await asyncio.wait_for(bot._handle_message(update, mock_context), timeout=30.0)
            except TimeoutError:
                log("Timeout waiting for response (30s)", "WARN")
                RESULTS["diagnostics"]["frictions"].append(f"Turn {turn}: Response timeout (>30s)")

            if captured_responses:
                response = captured_responses[-1]

                try:
                    new_state = tb.get_state(TEST_USER_ID)
                except:
                    new_state = "unknown"

                if new_state not in RESULTS["states_visited"]:
                    RESULTS["states_visited"].append(new_state)

                add_transcript(
                    turn,
                    "BOT",
                    response,
                    new_state,
                    {"has_buttons": len(captured_buttons) > 0, "response_count": len(captured_responses)},
                )

                # V4.2.1 FIX D: Check for emoji-only response
                if is_emoji_only_response(response):
                    RESULTS["diagnostics"]["emoji_only_responses"].append(f"Turn {turn}: {response[:50]}")
                    RESULTS["diagnostics"]["frictions"].append(
                        f"Turn {turn}: Emoji-only response (no text content)"
                    )
                    log("Emoji-only response detected!", "FAIL")
                    all_passed = False

                # V4.2.1 FIX D: Check for state regression
                if check_state_regression(previous_state, new_state, turn):
                    RESULTS["diagnostics"]["state_regressions"].append(
                        f"Turn {turn}: {previous_state} → {new_state}"
                    )
                    RESULTS["diagnostics"]["frictions"].append(
                        f"Turn {turn}: State regression ({previous_state} → {new_state})"
                    )
                    log(f"State regression: {previous_state} → {new_state}", "FAIL")
                    all_passed = False

                previous_state = new_state

                # Check for forbidden patterns
                forbidden = check_forbidden_patterns(response)
                if forbidden:
                    RESULTS["diagnostics"]["forbidden_patterns_found"].extend(forbidden)
                    RESULTS["diagnostics"]["frictions"].append(
                        f"Turn {turn}: Forbidden pattern(s) found: {forbidden}"
                    )
                    log(f"Forbidden pattern found: {forbidden}", "FAIL")
                    all_passed = False

                # Check for duplicates
                if response in previous_responses:
                    RESULTS["diagnostics"]["duplicates"].append(f"Turn {turn}: Duplicate response")
                    RESULTS["diagnostics"]["frictions"].append(f"Turn {turn}: Duplicate response detected")
                    log("Duplicate response detected", "WARN")

                previous_responses.append(response)

                analysis = analyze_response(response, turn)
                RESULTS["diagnostics"]["empathy_score"] += analysis["empathy_words"]
                RESULTS["diagnostics"]["clarity_score"] += analysis["clarity_score"]

                if len(captured_responses) > 3:
                    RESULTS["diagnostics"]["loops_detected"] = True
                    RESULTS["diagnostics"]["frictions"].append(
                        f"Turn {turn}: Multiple responses ({len(captured_responses)}) - potential loop"
                    )
                    log(f"Multiple responses detected: {len(captured_responses)}", "WARN")
                elif len(captured_responses) == 3:
                    log("3 responses (normal for onboarding flow)", "INFO")

            else:
                add_transcript(turn, "BOT", "(No response)", current_state)
                RESULTS["diagnostics"]["errors"].append(f"Turn {turn}: No response received")
                RESULTS["diagnostics"]["frictions"].append(f"Turn {turn}: Bot did not respond")
                log("No response received", "FAIL")
                all_passed = False

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            add_transcript(turn, "BOT", f"(ERROR: {error_msg})", current_state)
            RESULTS["diagnostics"]["errors"].append(f"Turn {turn}: {error_msg}")
            RESULTS["diagnostics"]["frictions"].append(f"Turn {turn}: Exception occurred")
            log(f"Exception: {error_msg}", "FAIL")
            RESULTS["diagnostics"]["forbidden_patterns_found"].append("Exception")
            all_passed = False

        await asyncio.sleep(0.1)

    if TEST_USER_ID in tb.user_data:
        del tb.user_data[TEST_USER_ID]

    RESULTS["end_time"] = datetime.now().isoformat()

    total_turns = len([t for t in RESULTS["transcript"] if t["role"] == "BOT"])
    if total_turns > 0:
        RESULTS["diagnostics"]["engagement_score"] = min(
            10, (RESULTS["diagnostics"]["empathy_score"] / total_turns) * 5 + 5
        )
        RESULTS["diagnostics"]["clarity_score"] = RESULTS["diagnostics"]["clarity_score"] / total_turns

    # Determine verdict - V4.2.1: Include emoji-only and state regression checks
    has_emoji_only = len(RESULTS["diagnostics"]["emoji_only_responses"]) > 0
    has_state_regression = len(RESULTS["diagnostics"]["state_regressions"]) > 0

    if (
        not all_passed
        or RESULTS["diagnostics"]["forbidden_patterns_found"]
        or RESULTS["diagnostics"]["errors"]
        or has_emoji_only
        or has_state_regression
    ):
        RESULTS["verdict"] = "NO-GO"
        if RESULTS["diagnostics"]["forbidden_patterns_found"]:
            RESULTS["actions_needed"].append("Fix forbidden patterns in responses")
        if RESULTS["diagnostics"]["errors"]:
            RESULTS["actions_needed"].append("Fix exceptions/errors in flow")
        if RESULTS["diagnostics"]["loops_detected"]:
            RESULTS["actions_needed"].append("Investigate potential response loops")
        if has_emoji_only:
            RESULTS["actions_needed"].append("Fix emoji-only responses (must have text content)")
        if has_state_regression:
            RESULTS["actions_needed"].append("Fix state regressions (state should not go backwards)")
    else:
        RESULTS["verdict"] = "GO"

    print_results()

    return all_passed and not has_emoji_only and not has_state_regression


def print_results():
    """Print comprehensive results"""

    print("\n" + "=" * 70)
    print("📊 SIMULATION RESULTS")
    print("=" * 70)

    print("\n" + "-" * 70)
    print("1️⃣ FULL TRANSCRIPT")
    print("-" * 70)

    for entry in RESULTS["transcript"]:
        role_icon = "👤" if entry["role"] == "USER" else "🤖"
        state_info = f" [{entry['state']}]" if entry["state"] else ""
        print(f"\nTurn {entry['turn']}{state_info}")
        print(
            f"{role_icon} {entry['role']}: {entry['message'][:300]}{'...' if len(entry['message']) > 300 else ''}"
        )

    print("\n" + "-" * 70)
    print("2️⃣ DIAGNOSTICS")
    print("-" * 70)

    diag = RESULTS["diagnostics"]

    print(f"\n📈 Engagement Score: {diag['engagement_score']:.1f}/10")
    print(f"📖 Clarity Score: {diag['clarity_score']:.1f}/10")
    print(f"💚 Empathy Words Found: {diag['empathy_score']}")

    print(f"\n🔀 States Visited: {len(RESULTS['states_visited'])}")
    for state in RESULTS["states_visited"]:
        print(f"   • {state}")

    if diag["frictions"]:
        print(f"\n⚡ Frictions ({len(diag['frictions'])}):")
        for f in diag["frictions"]:
            print(f"   • {f}")
    else:
        print("\n⚡ Frictions: None detected ✅")

    if diag["errors"]:
        print(f"\n❌ Errors ({len(diag['errors'])}):")
        for e in diag["errors"]:
            print(f"   • {e}")
    else:
        print("\n❌ Errors: None ✅")

    # V4.2.1 FIX D: Show emoji-only responses
    if diag["emoji_only_responses"]:
        print(f"\n🎭 Emoji-Only Responses ({len(diag['emoji_only_responses'])}):")
        for e in diag["emoji_only_responses"]:
            print(f"   • {e}")
    else:
        print("\n🎭 Emoji-Only Responses: None ✅")

    # V4.2.1 FIX D: Show state regressions
    if diag["state_regressions"]:
        print(f"\n⏪ State Regressions ({len(diag['state_regressions'])}):")
        for r in diag["state_regressions"]:
            print(f"   • {r}")
    else:
        print("\n⏪ State Regressions: None ✅")

    if diag["duplicates"]:
        print(f"\n🔄 Duplicates ({len(diag['duplicates'])}):")
        for d in diag["duplicates"]:
            print(f"   • {d}")
    else:
        print("\n🔄 Duplicates: None ✅")

    print(f"\n🔁 Loops Detected: {'Yes ⚠️' if diag['loops_detected'] else 'No ✅'}")

    print("\n" + "-" * 70)
    print("3️⃣ VALIDATION")
    print("-" * 70)

    validations = [
        ("⚠️ pattern", "⚠️" not in str(diag["forbidden_patterns_found"])),
        ("⏳ pattern", "⏳" not in str(diag["forbidden_patterns_found"])),
        ("Tracebacks", "Traceback" not in str(diag["forbidden_patterns_found"])),
        (
            "Exceptions",
            "Exception" not in str(diag["forbidden_patterns_found"])
            and "AttributeError" not in str(diag["forbidden_patterns_found"]),
        ),
        ("Loops", not diag["loops_detected"]),
        ("All responses received", len(diag["errors"]) == 0),
        ("No emoji-only responses", len(diag["emoji_only_responses"]) == 0),  # V4.2.1
        ("No state regressions", len(diag["state_regressions"]) == 0),  # V4.2.1
    ]

    for name, passed in validations:
        icon = "✅" if passed else "❌"
        print(f"   {icon} {name}: {'PASS' if passed else 'FAIL'}")

    if diag["forbidden_patterns_found"]:
        print(f"\n   ⚠️ Forbidden patterns found: {diag['forbidden_patterns_found']}")

    print("\n" + "-" * 70)
    print("4️⃣ CONCLUSION")
    print("-" * 70)

    verdict_icon = "✅" if RESULTS["verdict"] == "GO" else "❌"
    print(f"\n   {verdict_icon} VERDICT: {RESULTS['verdict']}")

    if RESULTS["actions_needed"]:
        print("\n   📋 Actions Needed:")
        for action in RESULTS["actions_needed"]:
            print(f"      • {action}")
    else:
        print("\n   📋 Actions Needed: None - Ready for production")

    print("\n" + "=" * 70)
    print(f"🏁 Simulation completed at {RESULTS['end_time']}")
    print("=" * 70 + "\n")


async def main():
    """Main entry point"""
    try:
        success = await run_simulation()
        return 0 if success else 1
    except Exception as e:
        import traceback

        print(f"\n❌ CRITICAL ERROR: {e}")
        print(traceback.format_exc())
        RESULTS["verdict"] = "NO-GO"
        RESULTS["diagnostics"]["errors"].append(f"Critical: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
