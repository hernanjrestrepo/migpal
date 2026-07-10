#!/usr/bin/env python3
"""
Test del módulo NeverSilent - SEGMENTO 2/4
Verifica que el bot NUNCA se quede callado
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.never_silent import WATCHDOG_TIMEOUT, AntiMultipleInstances, HealthCheck, get_never_silent


def test_recovery_messages():
    """Test que los mensajes de recuperación existen y son empáticos"""
    print("=" * 50)
    print("TEST 1: Recovery Messages")
    print("=" * 50)

    wrapper = get_never_silent()

    # Test español
    for i in range(5):
        msg = wrapper.get_recovery_message(12345, "es")
        assert msg, "Recovery message should not be empty"
        assert (
            "🙏" in msg or "😊" in msg or "💪" in msg or "🌟" in msg or "🤔" in msg
        ), f"Message should have emoji: {msg}"
        print(f"  ES #{i+1}: {msg[:50]}...")

    # Test inglés
    for i in range(5):
        msg = wrapper.get_recovery_message(12345, "en")
        assert msg, "Recovery message should not be empty"
        print(f"  EN #{i+1}: {msg[:50]}...")

    print("✅ TEST 1 PASSED: Recovery messages work\n")
    return True


def test_still_here_messages():
    """Test que los mensajes de 'sigo aquí' existen"""
    print("=" * 50)
    print("TEST 2: Still Here Messages")
    print("=" * 50)

    wrapper = get_never_silent()

    for lang in ["es", "en"]:
        for i in range(4):
            msg = wrapper.get_still_here_message(lang)
            assert msg, "Still here message should not be empty"
            assert (
                "⏳" in msg or "🔄" in msg or "⌛" in msg or "💭" in msg
            ), f"Message should have emoji: {msg}"
            print(f"  {lang.upper()} #{i+1}: {msg}")

    print("✅ TEST 2 PASSED: Still here messages work\n")
    return True


def test_watchdog_timeout():
    """Test que el timeout del watchdog es correcto"""
    print("=" * 50)
    print("TEST 3: Watchdog Timeout")
    print("=" * 50)

    assert WATCHDOG_TIMEOUT == 3.0, f"Watchdog timeout should be 3.0, got {WATCHDOG_TIMEOUT}"
    print(f"  Watchdog timeout: {WATCHDOG_TIMEOUT}s")

    print("✅ TEST 3 PASSED: Watchdog timeout is correct\n")
    return True


def test_anti_multiple_instances():
    """Test del sistema anti-múltiples instancias"""
    print("=" * 50)
    print("TEST 4: Anti Multiple Instances")
    print("=" * 50)

    # Verificar que podemos adquirir lock
    result = AntiMultipleInstances.acquire_lock()
    assert result, "Should be able to acquire lock"
    print("  ✅ Lock acquired")

    # Verificar que está bloqueado
    is_locked, pid = AntiMultipleInstances.is_locked()
    assert is_locked, "Should be locked"
    assert pid == os.getpid(), f"PID should match: {pid} vs {os.getpid()}"
    print(f"  ✅ Lock verified (PID: {pid})")

    # Liberar lock
    AntiMultipleInstances.release_lock()
    print("  ✅ Lock released")

    # Verificar que ya no está bloqueado
    is_locked, _ = AntiMultipleInstances.is_locked()
    assert not is_locked, "Should not be locked after release"
    print("  ✅ Lock verified as released")

    print("✅ TEST 4 PASSED: Anti multiple instances works\n")
    return True


async def test_healthcheck():
    """Test del sistema de healthcheck"""
    print("=" * 50)
    print("TEST 5: Health Check")
    print("=" * 50)

    # Ejecutar healthcheck
    status = await HealthCheck.full_check()

    print(f"  is_healthy: {status.is_healthy}")
    print(f"  single_instance: {status.single_instance}")
    print(f"  webhook_off: {status.webhook_off}")
    print(f"  polling_ok: {status.polling_ok}")
    print(f"  last_update_recent: {status.last_update_recent}")
    print(f"  pid: {status.pid}")
    print(f"  uptime: {status.uptime_seconds:.1f}s")

    if status.errors:
        print(f"  errors: {status.errors}")

    # Verificar formato
    formatted = HealthCheck.format_status(status)
    assert "MIGPAL BOT HEALTH CHECK" in formatted
    print("  ✅ Status format OK")

    print("✅ TEST 5 PASSED: Health check works\n")
    return True


def test_wrapper_decorator():
    """Test que el decorator funciona"""
    print("=" * 50)
    print("TEST 6: Wrapper Decorator")
    print("=" * 50)

    wrapper = get_never_silent()

    # Crear función de prueba
    async def test_handler(update, context):
        raise ValueError("Test error")

    # Envolver con never_silent
    wrapped = wrapper.wrap_handler(test_handler)

    assert wrapped.__name__ == "test_handler", "Should preserve function name"
    print("  ✅ Decorator preserves function name")

    print("✅ TEST 6 PASSED: Wrapper decorator works\n")
    return True


async def main():
    """Ejecutar todos los tests"""
    print("\n" + "=" * 60)
    print("🧪 NEVER SILENT MODULE TESTS - SEGMENTO 2/4")
    print("=" * 60 + "\n")

    results = []

    # Tests síncronos
    results.append(("Recovery Messages", test_recovery_messages()))
    results.append(("Still Here Messages", test_still_here_messages()))
    results.append(("Watchdog Timeout", test_watchdog_timeout()))
    results.append(("Anti Multiple Instances", test_anti_multiple_instances()))
    results.append(("Wrapper Decorator", test_wrapper_decorator()))

    # Tests asíncronos
    results.append(("Health Check", await test_healthcheck()))

    # Resumen
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
