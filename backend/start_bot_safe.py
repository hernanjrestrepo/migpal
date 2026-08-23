#!/usr/bin/env python3
"""
Script seguro para iniciar MigPAL v5.0
Maneja conflictos de múltiples instancias
"""

import os
import signal
import subprocess
import sys
import time


def kill_existing_processes():
    """Mata procesos existentes del bot"""
    print("🔍 Buscando procesos existentes...")
    try:
        # Buscar procesos Python relacionados con telegram
        result = subprocess.run(["pgrep", "-f", "run_telegram_bot.py"], capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid and pid != str(os.getpid()):
                    print(f"⚡ Matando proceso {pid}")
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except:
                        pass
            time.sleep(3)
    except Exception as e:
        print(f"⚠️ Error matando procesos: {e}")


def clear_locks():
    """Limpia archivos de lock"""
    print("🧹 Limpiando archivos de lock...")
    lock_files = ["data/migpal_bot.lock", "data/last_update.txt"]
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"✅ Eliminado: {lock_file}")
            except:
                pass

    # Resetear last_update
    try:
        with open("data/last_update.txt", "w") as f:
            f.write("0")
    except:
        pass


def wait_for_release():
    """Espera a que se libere el bot"""
    print("⏳ Esperando 30 segundos para que se libere el bot...")
    for i in range(30, 0, -1):
        print(f"\r⏳ Esperando: {i} segundos...", end="", flush=True)
        time.sleep(1)
    print("\n✅ Tiempo de espera completado")


def start_bot():
    """Inicia el bot"""
    print("\n🚀 Iniciando MigPAL v5.0...")
    print("=" * 50)

    # Activar entorno virtual si existe
    venv_activate = ".venv/bin/activate"
    if os.path.exists(venv_activate):
        activate_cmd = f"source {venv_activate} && "
    else:
        activate_cmd = ""

    # Iniciar el bot
    if activate_cmd:
        # Usar bash para source
        cmd = f'bash -c "{activate_cmd}python3 run_telegram_bot.py"'
    else:
        cmd = "python3 run_telegram_bot.py"
    subprocess.run(cmd, shell=True)


def main():
    print("🤖 MigPAL v5.0 - Inicio Seguro")
    print("=" * 50)

    # Cambiar al directorio del backend
    os.chdir("/workspace/hjrm/migpal/backend")

    # Ejecutar pasos de limpieza
    kill_existing_processes()
    clear_locks()
    wait_for_release()

    # Iniciar el bot
    start_bot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
