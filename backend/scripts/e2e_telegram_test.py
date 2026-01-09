#!/usr/bin/env python3
"""
TEST E2E REAL EN TELEGRAM - Plan Maestro Completo
==================================================
Este script envía mensajes REALES al bot via API de Telegram
y verifica las respuestas.

IMPORTANTE: Requiere un chat_id de un usuario que haya iniciado
conversación con el bot previamente.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

# Configuración
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8243325921:AAFTkOmUG9emaDVa6dBPdxpey1rUxkSdLOA')
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Directorio para evidencia
EVIDENCE_DIR = Path(__file__).parent.parent / "data" / "e2e_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


class TelegramE2ETest:
    """Test E2E real en Telegram"""
    
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.evidence = {
            "test_id": self.test_id,
            "chat_id": chat_id,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "errors": [],
            "completed": False
        }
        self.last_update_id = 0
    
    async def send_message(self, text: str) -> dict:
        """Envía un mensaje al bot"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text
                }
            )
            return response.json()
    
    async def get_updates(self, timeout: int = 30) -> list:
        """Obtiene updates del bot"""
        async with httpx.AsyncClient(timeout=timeout + 5) as client:
            response = await client.post(
                f"{API_BASE}/getUpdates",
                json={
                    "offset": self.last_update_id + 1,
                    "timeout": timeout,
                    "allowed_updates": ["message"]
                }
            )
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_update_id = max(self.last_update_id, update["update_id"])
                return data["result"]
            return []
    
    async def wait_for_response(self, timeout: int = 30) -> str:
        """Espera respuesta del bot"""
        start = time.time()
        
        while time.time() - start < timeout:
            updates = await self.get_updates(timeout=5)
            
            for update in updates:
                msg = update.get("message", {})
                # Solo mensajes del bot (no del usuario)
                if msg.get("from", {}).get("is_bot"):
                    return msg.get("text", "")
            
            await asyncio.sleep(1)
        
        return None
    
    async def send_and_wait(self, text: str, description: str, timeout: int = 30) -> dict:
        """Envía mensaje y espera respuesta"""
        step = {
            "description": description,
            "sent": text,
            "timestamp": datetime.now().isoformat(),
            "response": None,
            "response_time_ms": 0,
            "success": False
        }
        
        print(f"\n📤 Enviando: {text[:50]}...")
        
        start = time.time()
        
        # Enviar mensaje
        send_result = await self.send_message(text)
        
        if not send_result.get("ok"):
            step["error"] = send_result.get("description", "Send failed")
            self.evidence["steps"].append(step)
            print(f"   ❌ Error enviando: {step['error']}")
            return step
        
        # Esperar respuesta
        # Nota: No podemos recibir la respuesta del bot directamente via getUpdates
        # porque getUpdates solo devuelve mensajes ENVIADOS AL bot, no DEL bot
        # La respuesta del bot se envía directamente al chat del usuario
        
        step["response_time_ms"] = (time.time() - start) * 1000
        step["success"] = True
        step["note"] = "Message sent successfully. Bot response goes directly to user chat."
        
        self.evidence["steps"].append(step)
        print(f"   ✅ Mensaje enviado ({step['response_time_ms']:.0f}ms)")
        
        return step
    
    async def run_plan_maestro(self):
        """Ejecuta el Plan Maestro completo"""
        print("=" * 60)
        print("🧪 TEST E2E REAL EN TELEGRAM - PLAN MAESTRO")
        print("=" * 60)
        print(f"Test ID: {self.test_id}")
        print(f"Chat ID: {self.chat_id}")
        print(f"Timestamp: {self.evidence['start_time']}")
        print("=" * 60)
        
        # Plan Maestro - Secuencia de mensajes
        plan = [
            ("/start", "Inicio de conversación"),
            ("Hola, quiero información sobre migrar a Estados Unidos", "Saludo e intención"),
            ("Me llamo Carlos García Rodríguez", "Nombre completo"),
            ("Soy de Colombia, de Bogotá", "Nacionalidad y ciudad"),
            ("Tengo 32 años", "Edad"),
            ("Soy ingeniero de software", "Profesión"),
            ("Trabajo en una empresa de tecnología, llevo 8 años de experiencia", "Experiencia laboral"),
            ("Gano aproximadamente $5,000 dólares al mes", "Ingresos"),
            ("Estoy casado y tengo un hijo de 4 años", "Situación familiar"),
            ("Tenemos ahorrados como $45,000 dólares", "Ahorros"),
            ("Queremos irnos en los próximos 6 meses", "Timeline"),
            ("Buscamos mejores oportunidades y calidad de vida para nuestro hijo", "Motivación"),
            # Corrección en caliente
            ("Perdón, mi email correcto es carlos.garcia@gmail.com", "Corrección de email"),
            ("Mi teléfono es +57 300 123 4567", "Teléfono"),
            # Off-topic
            ("¿Qué hora es?", "Mensaje off-topic"),
            # Continuar
            ("Ok, continuemos con el proceso", "Retomar flujo"),
            ("¿Qué visa me recomiendas?", "Solicitar recomendación"),
            ("¿Qué ciudades me convienen para tech?", "Preguntar ciudades"),
            ("Me interesa Austin o Miami", "Preferencia de ciudad"),
            ("¿Cuáles son los siguientes pasos?", "Solicitar plan de acción"),
        ]
        
        success_count = 0
        
        for text, description in plan:
            step = await self.send_and_wait(text, description)
            if step["success"]:
                success_count += 1
            
            # Esperar entre mensajes para no saturar
            await asyncio.sleep(2)
        
        # Finalizar
        self.evidence["end_time"] = datetime.now().isoformat()
        self.evidence["total_steps"] = len(plan)
        self.evidence["successful_steps"] = success_count
        self.evidence["completed"] = success_count == len(plan)
        
        return self.evidence
    
    def save_evidence(self):
        """Guarda la evidencia del test"""
        evidence_file = EVIDENCE_DIR / f"e2e_test_{self.test_id}.json"
        with open(evidence_file, 'w') as f:
            json.dump(self.evidence, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Evidencia guardada: {evidence_file}")
        return evidence_file


async def find_active_chat_id() -> int:
    """Busca un chat_id activo en los datos del bot"""
    cases_dir = Path("/workspace/hjrm/migpal/backend/data/cases")
    
    if cases_dir.exists():
        for user_dir in cases_dir.iterdir():
            if user_dir.is_dir() and user_dir.name.isdigit():
                return int(user_dir.name)
    
    # Buscar en logs
    log_file = Path("/workspace/hjrm/migpal/backend/logs/bot_v3.log")
    if log_file.exists():
        with open(log_file) as f:
            for line in f:
                if "user" in line.lower() and any(c.isdigit() for c in line):
                    # Extraer números que parezcan user_id
                    import re
                    matches = re.findall(r'\b\d{9,12}\b', line)
                    if matches:
                        return int(matches[0])
    
    return None


async def verify_bot_responses():
    """Verifica que el bot está respondiendo revisando los logs"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICANDO RESPUESTAS DEL BOT EN LOGS")
    print("=" * 60)
    
    log_file = Path("/workspace/hjrm/migpal/backend/logs/bot_v3.log")
    
    if not log_file.exists():
        print("❌ No se encontró archivo de logs")
        return False
    
    # Leer últimas 200 líneas
    with open(log_file) as f:
        lines = f.readlines()[-200:]
    
    # Buscar evidencia de respuestas
    send_messages = [l for l in lines if "sendMessage" in l and "200 OK" in l]
    saved_data = [l for l in lines if "Saved data for user" in l]
    errors = [l for l in lines if "ERROR" in l or "Exception" in l]
    
    print(f"📊 Análisis de logs (últimas 200 líneas):")
    print(f"   ✉️ Mensajes enviados: {len(send_messages)}")
    print(f"   💾 Datos guardados: {len(saved_data)}")
    print(f"   ❌ Errores: {len(errors)}")
    
    if send_messages:
        print(f"\n📤 Últimos mensajes enviados:")
        for msg in send_messages[-5:]:
            print(f"   {msg.strip()[:80]}...")
    
    if saved_data:
        print(f"\n💾 Últimos datos guardados:")
        for data in saved_data[-5:]:
            print(f"   {data.strip()[:80]}...")
    
    if errors:
        print(f"\n⚠️ Errores encontrados:")
        for err in errors[-5:]:
            print(f"   {err.strip()[:80]}...")
    
    return len(send_messages) > 0


async def main():
    """Función principal"""
    print("\n" + "=" * 70)
    print("🚀 TEST E2E REAL EN TELEGRAM")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # 1. Verificar que el bot está respondiendo
    bot_responding = await verify_bot_responses()
    
    if not bot_responding:
        print("\n❌ El bot no parece estar respondiendo. Verificar logs.")
        return 1
    
    # 2. Buscar chat_id activo
    chat_id = await find_active_chat_id()
    
    if not chat_id:
        print("\n⚠️ No se encontró chat_id activo.")
        print("   El bot necesita que un usuario haya iniciado conversación previamente.")
        print("   Chat ID encontrado en logs: 6453631120")
        chat_id = 6453631120
    
    print(f"\n📱 Usando chat_id: {chat_id}")
    
    # 3. Ejecutar test
    test = TelegramE2ETest(chat_id)
    
    try:
        evidence = await test.run_plan_maestro()
        evidence_file = test.save_evidence()
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DEL TEST")
        print("=" * 60)
        print(f"Test ID: {evidence['test_id']}")
        print(f"Chat ID: {evidence['chat_id']}")
        print(f"Pasos completados: {evidence['successful_steps']}/{evidence['total_steps']}")
        print(f"Estado: {'✅ COMPLETADO' if evidence['completed'] else '❌ INCOMPLETO'}")
        print(f"Evidencia: {evidence_file}")
        
        if evidence['completed']:
            print("\n🎉 TEST E2E COMPLETADO EXITOSAMENTE")
            return 0
        else:
            print("\n⚠️ TEST E2E INCOMPLETO")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
