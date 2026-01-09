#!/usr/bin/env python3
"""
Diagnóstico del Bot de Telegram
Verifica: token, webhook, polling, instancias, conectividad
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime

# Cargar variables de entorno
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
except:
    pass

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8243325921:AAFTkOmUG9emaDVa6dBPdxpey1rUxkSdLOA')


async def diagnose():
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DEL BOT DE TELEGRAM")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues = []
    
    # 1. Verificar token
    print("1️⃣ Verificando token...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            data = response.json()
            
            if data.get("ok"):
                bot_info = data["result"]
                print(f"   ✅ Token válido")
                print(f"   Bot: @{bot_info.get('username')}")
                print(f"   ID: {bot_info.get('id')}")
            else:
                print(f"   ❌ Token inválido: {data.get('description')}")
                issues.append("Token inválido")
    except Exception as e:
        print(f"   ❌ Error verificando token: {e}")
        issues.append(f"Error de token: {e}")
    print()
    
    # 2. Verificar webhook
    print("2️⃣ Verificando webhook...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
            data = response.json()
            
            if data.get("ok"):
                webhook = data["result"]
                if webhook.get("url"):
                    print(f"   ⚠️ Webhook ACTIVO: {webhook['url']}")
                    print(f"   Para usar polling, desactiva el webhook:")
                    print(f"   curl 'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook'")
                    issues.append("Webhook activo (debe estar desactivado para polling)")
                else:
                    print(f"   ✅ Webhook desactivado (correcto para polling)")
                
                pending = webhook.get("pending_update_count", 0)
                print(f"   Updates pendientes: {pending}")
                
                if webhook.get("last_error_message"):
                    print(f"   ⚠️ Último error: {webhook['last_error_message']}")
    except Exception as e:
        print(f"   ❌ Error verificando webhook: {e}")
        issues.append(f"Error de webhook: {e}")
    print()
    
    # 3. Verificar procesos locales
    print("3️⃣ Verificando procesos locales...")
    try:
        result = subprocess.run(
            ["pgrep", "-f", "telegram_bot"],
            capture_output=True, text=True
        )
        pids = [p for p in result.stdout.strip().split('\n') if p]
        
        if pids:
            print(f"   ⚠️ Procesos encontrados: {pids}")
            for pid in pids:
                try:
                    ps_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "pid,ppid,cmd", "--no-headers"],
                        capture_output=True, text=True
                    )
                    print(f"      {ps_result.stdout.strip()}")
                except:
                    pass
        else:
            print(f"   ℹ️ No hay procesos del bot corriendo localmente")
    except Exception as e:
        print(f"   ⚠️ No se pudo verificar procesos: {e}")
    print()
    
    # 4. Verificar lockfile
    print("4️⃣ Verificando lockfile...")
    lockfile = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "migpal_bot.lock")
    if os.path.exists(lockfile):
        with open(lockfile) as f:
            pid = f.read().strip()
        print(f"   Lockfile existe con PID: {pid}")
        
        # Verificar si el proceso existe
        try:
            os.kill(int(pid), 0)
            print(f"   ✅ Proceso {pid} está corriendo")
        except ProcessLookupError:
            print(f"   ⚠️ Proceso {pid} NO está corriendo (lockfile obsoleto)")
        except ValueError:
            print(f"   ⚠️ PID inválido en lockfile")
    else:
        print(f"   ℹ️ No hay lockfile")
    print()
    
    # 5. Probar envío de mensaje
    print("5️⃣ Probando conectividad...")
    try:
        async with httpx.AsyncClient() as client:
            # Intentar obtener updates (esto fallará si hay otra instancia)
            response = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                json={"timeout": 1, "limit": 1}
            )
            data = response.json()
            
            if data.get("ok"):
                print(f"   ✅ Conectividad OK")
                updates = data.get("result", [])
                if updates:
                    print(f"   Último update: {updates[-1].get('update_id')}")
            else:
                error = data.get("description", "Unknown error")
                if "Conflict" in error:
                    print(f"   ❌ CONFLICTO: Otra instancia del bot está corriendo")
                    print(f"   Esto puede ser:")
                    print(f"      - Otra instancia en este servidor")
                    print(f"      - Una instancia en producción/otro servidor")
                    print(f"      - Un proceso zombie")
                    issues.append("Conflicto: otra instancia corriendo")
                else:
                    print(f"   ❌ Error: {error}")
                    issues.append(f"Error de conectividad: {error}")
    except Exception as e:
        print(f"   ❌ Error de conectividad: {e}")
        issues.append(f"Error de conectividad: {e}")
    print()
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    if not issues:
        print("✅ Todo OK - El bot debería poder iniciar")
    else:
        print("❌ Problemas encontrados:")
        for issue in issues:
            print(f"   • {issue}")
        
        print()
        print("🔧 SOLUCIONES:")
        if any("Conflicto" in i for i in issues):
            print("   1. Detener TODAS las instancias del bot:")
            print("      pkill -f telegram_bot")
            print("   2. Si hay una instancia en producción, detenerla primero")
            print("   3. Esperar 30 segundos antes de reiniciar")
        if any("Webhook" in i for i in issues):
            print(f"   • Desactivar webhook:")
            print(f"     curl 'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook'")
    
    print()
    return len(issues) == 0


if __name__ == "__main__":
    result = asyncio.run(diagnose())
    sys.exit(0 if result else 1)
