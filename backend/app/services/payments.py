"""
MigPAL Payment System
Sistema de pagos para el proceso migratorio

Soporta:
- Stripe (tarjetas)
- PayPal
- Transferencia bancaria (manual)

Precios:
- Diagnóstico: $50 USD
- Aprobación: $50 USD
- Plan Completo: $900 USD
- Total: $1,000 USD
- Devolución máxima: $800 USD
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import json
import hashlib
import hmac

logger = logging.getLogger(__name__)

# ============== CONFIGURACIÓN ==============

# Stripe (configurar en .env)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# PayPal (configurar en .env)
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox o live

# Cuenta bancaria para transferencias
BANK_INFO = {
    "bank": "Bank of America",
    "account_name": "MigPAL LLC",
    "account_number": "****1234",
    "routing": "****5678",
    "swift": "BOFAUS3N",
    "zelle": "pagos@migpal.com",
}

# ============== TIPOS DE PAGO ==============

class PaymentType(Enum):
    DIAGNOSTICO = "diagnostico"
    APROBACION = "aprobacion"
    PLAN_COMPLETO = "plan_completo"
    REFUND = "refund"

class PaymentMethod(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    ZELLE = "zelle"
    CRYPTO = "crypto"

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

# ============== PRECIOS ==============

PRICES = {
    PaymentType.DIAGNOSTICO: 50,
    PaymentType.APROBACION: 50,
    PaymentType.PLAN_COMPLETO: 900,
}

REFUND_AMOUNT = 800
RETENTION_AMOUNT = 200  # Gastos legales e impuestos

# ============== REGISTRO DE PAGOS ==============

class PaymentRecord:
    """Registro de un pago"""
    
    def __init__(
        self,
        user_id: int,
        payment_type: PaymentType,
        amount: float,
        method: PaymentMethod = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        transaction_id: str = None,
        metadata: Dict = None
    ):
        self.id = self._generate_id(user_id)
        self.user_id = user_id
        self.payment_type = payment_type
        self.amount = amount
        self.method = method
        self.status = status
        self.transaction_id = transaction_id
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def _generate_id(self, user_id: int) -> str:
        """Genera ID único para el pago"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PAY-{user_id}-{timestamp}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "payment_type": self.payment_type.value,
            "amount": self.amount,
            "method": self.method.value if self.method else None,
            "status": self.status.value,
            "transaction_id": self.transaction_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ============== PAYMENT MANAGER ==============

class PaymentManager:
    """Gestor de pagos de MigPAL"""
    
    def __init__(self):
        self._payments: Dict[str, PaymentRecord] = {}
        self._user_payments: Dict[int, list] = {}
    
    # ============== CREAR PAGO ==============
    
    def create_payment(
        self,
        user_id: int,
        payment_type: PaymentType,
        method: PaymentMethod = None
    ) -> PaymentRecord:
        """Crea un nuevo registro de pago"""
        amount = PRICES.get(payment_type, 0)
        
        record = PaymentRecord(
            user_id=user_id,
            payment_type=payment_type,
            amount=amount,
            method=method
        )
        
        self._payments[record.id] = record
        
        if user_id not in self._user_payments:
            self._user_payments[user_id] = []
        self._user_payments[user_id].append(record.id)
        
        logger.info(f"Payment created: {record.id} for user {user_id}")
        return record
    
    # ============== LINKS DE PAGO ==============
    
    def get_payment_link(
        self,
        user_id: int,
        payment_type: PaymentType,
        method: PaymentMethod
    ) -> Tuple[str, str]:
        """
        Genera link de pago según el método
        Returns: (payment_id, payment_url)
        """
        record = self.create_payment(user_id, payment_type, method)
        amount = record.amount
        
        if method == PaymentMethod.STRIPE:
            url = self._create_stripe_link(record)
        elif method == PaymentMethod.PAYPAL:
            url = self._create_paypal_link(record)
        elif method == PaymentMethod.ZELLE:
            url = self._get_zelle_instructions(record)
        elif method == PaymentMethod.BANK_TRANSFER:
            url = self._get_bank_instructions(record)
        else:
            url = None
        
        return record.id, url
    
    def _create_stripe_link(self, record: PaymentRecord) -> str:
        """Crea link de Stripe Checkout"""
        # En producción, usar Stripe API
        # Por ahora, retornar instrucciones
        return f"https://buy.stripe.com/migpal_{record.payment_type.value}_{record.amount}"
    
    def _create_paypal_link(self, record: PaymentRecord) -> str:
        """Crea link de PayPal"""
        # En producción, usar PayPal API
        return f"https://paypal.me/migpal/{record.amount}"
    
    def _get_zelle_instructions(self, record: PaymentRecord) -> str:
        """Instrucciones para Zelle"""
        return f"""💳 *PAGO POR ZELLE*

Envía ${record.amount} USD a:
📧 *{BANK_INFO['zelle']}*

Incluye en el memo:
`{record.id}`

Una vez enviado, confirma aquí."""
    
    def _get_bank_instructions(self, record: PaymentRecord) -> str:
        """Instrucciones para transferencia bancaria"""
        return f"""🏦 *TRANSFERENCIA BANCARIA*

Banco: {BANK_INFO['bank']}
Nombre: {BANK_INFO['account_name']}
Cuenta: {BANK_INFO['account_number']}
Routing: {BANK_INFO['routing']}
SWIFT: {BANK_INFO['swift']}

Monto: ${record.amount} USD
Referencia: `{record.id}`

Una vez enviado, confirma aquí."""
    
    # ============== CONFIRMAR PAGO ==============
    
    def confirm_payment(
        self,
        payment_id: str,
        transaction_id: str = None,
        metadata: Dict = None
    ) -> Tuple[bool, str]:
        """Confirma un pago como completado"""
        if payment_id not in self._payments:
            return False, "Pago no encontrado"
        
        record = self._payments[payment_id]
        record.status = PaymentStatus.COMPLETED
        record.transaction_id = transaction_id
        record.updated_at = datetime.now().isoformat()
        
        if metadata:
            record.metadata.update(metadata)
        
        logger.info(f"Payment confirmed: {payment_id}")
        return True, f"✅ Pago confirmado: ${record.amount} USD"
    
    def fail_payment(self, payment_id: str, reason: str = None) -> Tuple[bool, str]:
        """Marca un pago como fallido"""
        if payment_id not in self._payments:
            return False, "Pago no encontrado"
        
        record = self._payments[payment_id]
        record.status = PaymentStatus.FAILED
        record.updated_at = datetime.now().isoformat()
        record.metadata["failure_reason"] = reason
        
        logger.info(f"Payment failed: {payment_id} - {reason}")
        return True, f"❌ Pago fallido: {reason}"
    
    # ============== DEVOLUCIONES ==============
    
    def create_refund(
        self,
        user_id: int,
        reason: str,
        amount: float = None
    ) -> Tuple[bool, str, str]:
        """
        Crea una solicitud de devolución
        Returns: (success, message, refund_id)
        """
        refund_amount = amount or REFUND_AMOUNT
        
        # Verificar que el usuario haya pagado suficiente
        total_paid = self.get_user_total_paid(user_id)
        if total_paid < refund_amount:
            refund_amount = total_paid
        
        if refund_amount <= 0:
            return False, "No hay pagos para devolver", None
        
        record = PaymentRecord(
            user_id=user_id,
            payment_type=PaymentType.REFUND,
            amount=-refund_amount,
            status=PaymentStatus.PENDING,
            metadata={"reason": reason}
        )
        
        self._payments[record.id] = record
        
        if user_id not in self._user_payments:
            self._user_payments[user_id] = []
        self._user_payments[user_id].append(record.id)
        
        logger.info(f"Refund requested: {record.id} for ${refund_amount}")
        return True, f"Devolución solicitada: ${refund_amount} USD", record.id
    
    def process_refund(self, refund_id: str) -> Tuple[bool, str]:
        """Procesa una devolución (admin)"""
        if refund_id not in self._payments:
            return False, "Devolución no encontrada"
        
        record = self._payments[refund_id]
        record.status = PaymentStatus.REFUNDED
        record.updated_at = datetime.now().isoformat()
        
        logger.info(f"Refund processed: {refund_id}")
        return True, f"✅ Devolución procesada: ${abs(record.amount)} USD"
    
    # ============== CONSULTAS ==============
    
    def get_payment(self, payment_id: str) -> Optional[PaymentRecord]:
        """Obtiene un pago por ID"""
        return self._payments.get(payment_id)
    
    def get_user_payments(self, user_id: int) -> list:
        """Obtiene todos los pagos de un usuario"""
        payment_ids = self._user_payments.get(user_id, [])
        return [self._payments[pid] for pid in payment_ids if pid in self._payments]
    
    def get_user_total_paid(self, user_id: int) -> float:
        """Obtiene el total pagado por un usuario"""
        payments = self.get_user_payments(user_id)
        return sum(
            p.amount for p in payments 
            if p.status == PaymentStatus.COMPLETED and p.amount > 0
        )
    
    def get_payment_status_display(self, user_id: int) -> str:
        """Genera display del estado de pagos"""
        payments = self.get_user_payments(user_id)
        total_paid = self.get_user_total_paid(user_id)
        
        lines = ["💳 *HISTORIAL DE PAGOS*\n"]
        
        if not payments:
            lines.append("No tienes pagos registrados.")
        else:
            for p in payments:
                status_emoji = {
                    PaymentStatus.PENDING: "⏳",
                    PaymentStatus.PROCESSING: "🔄",
                    PaymentStatus.COMPLETED: "✅",
                    PaymentStatus.FAILED: "❌",
                    PaymentStatus.REFUNDED: "💸",
                    PaymentStatus.CANCELLED: "🚫",
                }.get(p.status, "❓")
                
                amount_str = f"${abs(p.amount)}"
                if p.amount < 0:
                    amount_str = f"-{amount_str} (devolución)"
                
                lines.append(f"{status_emoji} {p.payment_type.value}: {amount_str}")
        
        lines.append(f"\n💰 *Total pagado:* ${total_paid} USD")
        
        return "\n".join(lines)


# ============== SINGLETON ==============

_payment_manager: Optional[PaymentManager] = None

def get_payment_manager() -> PaymentManager:
    """Obtiene instancia del gestor de pagos"""
    global _payment_manager
    if _payment_manager is None:
        _payment_manager = PaymentManager()
    return _payment_manager


# ============== HELPERS ==============

def get_payment_options_keyboard(payment_type: PaymentType) -> list:
    """Genera opciones de pago para teclado"""
    amount = PRICES.get(payment_type, 0)
    
    return [
        [("💳 Tarjeta (Stripe)", f"pay_stripe_{payment_type.value}")],
        [("🅿️ PayPal", f"pay_paypal_{payment_type.value}")],
        [("📱 Zelle", f"pay_zelle_{payment_type.value}")],
        [("🏦 Transferencia", f"pay_bank_{payment_type.value}")],
    ]

def get_payment_summary() -> str:
    """Resumen de métodos de pago"""
    return """💳 *MÉTODOS DE PAGO*

• *Tarjeta* (Visa, Mastercard, Amex)
• *PayPal*
• *Zelle* (USA)
• *Transferencia bancaria*

🔒 Todos los pagos son seguros y encriptados.
📧 Soporte: pagos@migpal.com"""
