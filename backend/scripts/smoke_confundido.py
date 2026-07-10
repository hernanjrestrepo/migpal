#!/usr/bin/env python3
"""
SMOKE TEST: Confundido Flow
============================
Simula el flujo de un usuario que dice "Confundido" durante onboarding.
Verifica que NO aparezca "⚠️" ni "⏳ Sigo aquí…" (error de timeout).

Ejecutar: python scripts/smoke_confundido.py
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test results
RESULTS = {
    "test_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
    "passed": False,
    "steps": [],
    "errors": [],
    "responses": [],
    "forbidden_patterns": ["⚠️", "⏳ Sigo aquí", "Traceback", "AttributeError", "KeyError", "'NoneType'"],
}


def log_step(step: str, status: str = "INFO"):
    """Log a test step"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔹"
    print(f"{icon} [{timestamp}] {step}")
    RESULTS["steps"].append({"time": timestamp, "step": step, "status": status})


def check_response(response: str, step_name: str) -> bool:
    """Check response for forbidden patterns"""
    if not response:
        log_step(f"{step_name}: No response received", "FAIL")
        RESULTS["errors"].append(f"{step_name}: No response")
        return False

    RESULTS["responses"].append({"step": step_name, "response": response[:500]})

    for pattern in RESULTS["forbidden_patterns"]:
        if pattern in response:
            log_step(f"{step_name}: Found forbidden pattern '{pattern}'", "FAIL")
            RESULTS["errors"].append(f"Found '{pattern}' in response")
            return False

    log_step(f"{step_name}: Response OK ({len(response)} chars)", "PASS")
    return True


async def run_smoke_test():
    """Run the smoke test simulating Telegram messages"""

    print("\n" + "=" * 60)
    print("🧪 SMOKE TEST: Confundido Flow")
    print("=" * 60 + "\n")

    log_step("Importing bot modules...")

    try:
        # Import the module to access its globals
        from app.services import telegram_bot as tb
        from app.services.onboarding_v306 import OnboardingState

        log_step("Modules imported successfully", "PASS")
    except Exception as e:
        import traceback

        log_step(f"Import failed: {e}", "FAIL")
        RESULTS["errors"].append(str(e))
        RESULTS["errors"].append(traceback.format_exc())
        return False

    # Test user ID (fake)
    TEST_USER_ID = 999999999

    # Create bot instance for testing
    log_step("Creating bot instance...")
    try:
        bot = tb.MigPALBot()
        log_step("Bot instance created", "PASS")
    except Exception as e:
        log_step(f"Bot creation failed: {e}", "FAIL")
        RESULTS["errors"].append(str(e))
        return False

    # Clean up any existing state for test user
    if TEST_USER_ID in tb.user_data:
        del tb.user_data[TEST_USER_ID]

    # Captured responses
    captured_responses = []

    # Mock the Update and Message objects
    def create_mock_update(text: str = None, callback_data: str = None):
        mock_update = MagicMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = TEST_USER_ID
        mock_update.effective_user.first_name = "TestUser"
        mock_update.effective_user.language_code = "es"

        if text:
            mock_update.message = MagicMock()
            mock_update.message.text = text
            mock_update.message.from_user = mock_update.effective_user

            async def capture_reply(msg, **kwargs):
                captured_responses.append(msg)
                return MagicMock()

            mock_update.message.reply_text = AsyncMock(side_effect=capture_reply)
            mock_update.callback_query = None

        if callback_data:
            mock_update.callback_query = MagicMock()
            mock_update.callback_query.data = callback_data
            mock_update.callback_query.from_user = mock_update.effective_user
            mock_update.callback_query.answer = AsyncMock()

            async def capture_edit(msg, **kwargs):
                captured_responses.append(msg)
                return MagicMock()

            mock_update.callback_query.edit_message_text = AsyncMock(side_effect=capture_edit)
            mock_update.callback_query.message = MagicMock()
            mock_update.callback_query.message.reply_text = AsyncMock(side_effect=capture_edit)
            mock_update.message = None

        return mock_update

    mock_context = MagicMock()
    mock_context.bot = MagicMock()
    mock_context.bot.send_message = AsyncMock()

    all_passed = True

    # ========== TEST 1: Setup initial state ==========
    log_step("TEST 1: Setting up initial state (simulating post-/start)...")
    try:
        # Set initial state as if user just did /start and is in onboarding question phase
        # Using the correct OnboardingState enum
        tb.set_state(TEST_USER_ID, OnboardingState.OPEN_QUESTION.value)

        # Initialize user_data with required structure
        tb.user_data[TEST_USER_ID] = {
            "user_id": TEST_USER_ID,
            "lang": "es",
            "language": "es",
            "name": "TestUser",
            "state": OnboardingState.OPEN_QUESTION.value,
            "profile": {
                "personal": {"name": "TestUser"},
                "education": {},
                "work": {},
                "languages": {},
                "history": {},
                "financial": {},
            },
            "family_members": [],
            "current_family_index": 0,
            "preferences": {},
            "selected_route": {},
            "documents": [],
        }
        log_step(f"Initial state set: {OnboardingState.OPEN_QUESTION.value}", "PASS")
    except Exception as e:
        import traceback

        log_step(f"Setup failed: {e}", "FAIL")
        RESULTS["errors"].append(str(e))
        RESULTS["errors"].append(traceback.format_exc())
        all_passed = False

    # ========== TEST 2: "Confundido" ==========
    log_step("TEST 2: Sending 'Confundido' message...")
    try:
        captured_responses.clear()
        update = create_mock_update(text="Confundido")

        await bot._handle_message(update, mock_context)

        if captured_responses:
            response = captured_responses[-1]
            if not check_response(response, "Confundido"):
                all_passed = False
            else:
                # Verify we got a helpful response, not an error
                response_lower = response.lower()
                if any(
                    word in response_lower
                    for word in ["tranquilo", "normal", "ayud", "entiendo", "paso", "bien", "aquí"]
                ):
                    log_step("Response contains empathetic content ✓", "PASS")
                else:
                    log_step(f"Response preview: {response[:200]}...", "INFO")
        else:
            log_step("Confundido: No response captured", "FAIL")
            all_passed = False

    except Exception as e:
        import traceback

        log_step(f"Confundido failed: {type(e).__name__}: {e}", "FAIL")
        RESULTS["errors"].append(f"Confundido: {e}")
        RESULTS["errors"].append(traceback.format_exc())
        all_passed = False

    # ========== TEST 3: "Que no se ni por donde comenzar" ==========
    log_step("TEST 3: Sending 'Que no se ni por donde comenzar'...")
    try:
        captured_responses.clear()
        update = create_mock_update(text="Que no se ni por donde comenzar")

        await bot._handle_message(update, mock_context)

        if captured_responses:
            response = captured_responses[-1]
            if not check_response(response, "No sé por dónde"):
                all_passed = False
        else:
            log_step("No sé por dónde: No response captured", "FAIL")
            all_passed = False

    except Exception as e:
        import traceback

        log_step(f"No sé por dónde failed: {type(e).__name__}: {e}", "FAIL")
        RESULTS["errors"].append(f"No sé por dónde: {e}")
        RESULTS["errors"].append(traceback.format_exc())
        all_passed = False

    # ========== CLEANUP ==========
    if TEST_USER_ID in tb.user_data:
        del tb.user_data[TEST_USER_ID]

    # ========== RESULTS ==========
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)

    RESULTS["passed"] = all_passed

    if all_passed:
        print("✅ ALL TESTS PASSED - No forbidden patterns found")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nErrors:")
        for err in RESULTS["errors"]:
            print(f"  - {err[:300]}")

    print("\n📝 Responses captured:")
    for r in RESULTS["responses"]:
        preview = r["response"][:150].replace("\n", " ")
        print(f"  [{r['step']}]: {preview}...")

    print("\n" + "=" * 60)

    return all_passed


async def main():
    """Main entry point"""
    try:
        success = await run_smoke_test()
        return 0 if success else 1
    except Exception as e:
        import traceback

        print(f"\n❌ CRITICAL ERROR: {e}")
        print(traceback.format_exc())
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
