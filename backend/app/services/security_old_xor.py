"""
MigPAL Security Module
Encriptación, validación y rate limiting para proteger datos de usuarios

Features:
- Encriptación de datos sensibles (email, teléfono)
- Validación de inputs
- Rate limiting por usuario
- Sanitización de datos
"""

import os
import re
import time
import hashlib
import base64
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)

# ============== ENCRYPTION ==============

# Simple encryption key (in production, use proper key management)
ENCRYPTION_KEY = os.getenv("MIGPAL_ENCRYPTION_KEY", "migpal_default_key_change_in_production_2026")

def _get_cipher_key() -> bytes:
    """Get a 32-byte key for encryption"""
    return hashlib.sha256(ENCRYPTION_KEY.encode()).digest()

def encrypt_sensitive(data: str) -> str:
    """
    Encrypt sensitive data using XOR cipher with base64 encoding.
    For production, use proper encryption like Fernet from cryptography library.
    """
    if not data:
        return data
    
    try:
        key = _get_cipher_key()
        encrypted = bytes([ord(c) ^ key[i % len(key)] for i, c in enumerate(data)])
        return "ENC:" + base64.b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return data

def decrypt_sensitive(data: str) -> str:
    """Decrypt sensitive data"""
    if not data or not data.startswith("ENC:"):
        return data
    
    try:
        key = _get_cipher_key()
        encrypted = base64.b64decode(data[4:])
        decrypted = ''.join([chr(b ^ key[i % len(key)]) for i, b in enumerate(encrypted)])
        return decrypted
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return data

def hash_identifier(identifier: str) -> str:
    """Create a one-way hash of an identifier (for logging without exposing data)"""
    return hashlib.sha256(identifier.encode()).hexdigest()[:12]

# ============== SENSITIVE FIELDS ==============

SENSITIVE_FIELDS = [
    "email", "phone", "passport_number", "ssn", "sin",
    "bank_account", "credit_card", "address"
]

def encrypt_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive fields in user data"""
    if not isinstance(data, dict):
        return data
    
    encrypted = data.copy()
    
    def encrypt_recursive(obj: Any, path: str = "") -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key.lower() in SENSITIVE_FIELDS:
                    if isinstance(value, str) and not value.startswith("ENC:"):
                        result[key] = encrypt_sensitive(value)
                    else:
                        result[key] = value
                else:
                    result[key] = encrypt_recursive(value, current_path)
            return result
        elif isinstance(obj, list):
            return [encrypt_recursive(item, path) for item in obj]
        else:
            return obj
    
    return encrypt_recursive(encrypted)

def decrypt_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive fields in user data"""
    if not isinstance(data, dict):
        return data
    
    def decrypt_recursive(obj: Any) -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("ENC:"):
                    result[key] = decrypt_sensitive(value)
                else:
                    result[key] = decrypt_recursive(value)
            return result
        elif isinstance(obj, list):
            return [decrypt_recursive(item) for item in obj]
        else:
            return obj
    
    return decrypt_recursive(data)

# ============== INPUT VALIDATION ==============

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    if not email:
        return True, ""  # Empty is OK (optional field)
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, email.lower().strip()
    return False, "Formato de email inválido"

def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate phone number"""
    if not phone:
        return True, ""
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone)
    
    # Check if it's a valid phone (7-15 digits, optionally starting with +)
    if re.match(r'^\+?[0-9]{7,15}$', cleaned):
        return True, cleaned
    return False, "Formato de teléfono inválido"

def validate_date(date_str: str) -> Tuple[bool, str]:
    """Validate date format (DD/MM/YYYY or YYYY-MM-DD)"""
    if not date_str:
        return True, ""
    
    # Try different formats
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # Check reasonable date range (1900-2100)
            if 1900 <= parsed.year <= 2100:
                return True, parsed.strftime("%d/%m/%Y")
        except ValueError:
            continue
    
    return False, "Formato de fecha inválido (usa DD/MM/YYYY)"

def validate_name(name: str) -> Tuple[bool, str]:
    """Validate name (no special characters except spaces and hyphens)"""
    if not name:
        return False, "El nombre es requerido"
    
    # Allow letters, spaces, hyphens, apostrophes, and accented characters
    if re.match(r"^[\p{L}\s\-'\.]+$", name, re.UNICODE) or re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-'\.]+$", name):
        cleaned = ' '.join(name.split())  # Normalize whitespace
        if 2 <= len(cleaned) <= 100:
            return True, cleaned.title()
    
    return False, "Nombre inválido (solo letras, espacios y guiones)"

def validate_text_input(text: str, max_length: int = 500) -> Tuple[bool, str]:
    """Validate general text input"""
    if not text:
        return True, ""
    
    # Remove potentially dangerous characters
    cleaned = re.sub(r'[<>{}]', '', text)
    
    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return True, cleaned.strip()

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Remove potential HTML/script tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        r';\s*DROP\s+', r';\s*DELETE\s+', r';\s*UPDATE\s+',
        r';\s*INSERT\s+', r'--', r'/\*', r'\*/'
    ]
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

# ============== RATE LIMITING ==============

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[int, list] = defaultdict(list)
        self.blocked_until: Dict[int, datetime] = {}
        
        # Configuration
        self.max_requests_per_minute = 30
        self.max_requests_per_hour = 200
        self.block_duration_minutes = 5
    
    def is_allowed(self, user_id: int) -> Tuple[bool, str]:
        """Check if user is allowed to make a request"""
        now = datetime.now()
        
        # Check if user is blocked
        if user_id in self.blocked_until:
            if now < self.blocked_until[user_id]:
                remaining = (self.blocked_until[user_id] - now).seconds
                return False, f"⏳ Demasiadas solicitudes. Espera {remaining} segundos."
            else:
                del self.blocked_until[user_id]
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > hour_ago
        ]
        
        # Count recent requests
        requests_last_minute = sum(1 for t in self.requests[user_id] if t > minute_ago)
        requests_last_hour = len(self.requests[user_id])
        
        # Check limits
        if requests_last_minute >= self.max_requests_per_minute:
            self.blocked_until[user_id] = now + timedelta(minutes=self.block_duration_minutes)
            logger.warning(f"User {hash_identifier(str(user_id))} rate limited (minute)")
            return False, "⏳ Demasiadas solicitudes por minuto. Espera un momento."
        
        if requests_last_hour >= self.max_requests_per_hour:
            self.blocked_until[user_id] = now + timedelta(minutes=self.block_duration_minutes * 2)
            logger.warning(f"User {hash_identifier(str(user_id))} rate limited (hour)")
            return False, "⏳ Demasiadas solicitudes por hora. Espera unos minutos."
        
        # Record this request
        self.requests[user_id].append(now)
        return True, ""
    
    def get_stats(self, user_id: int) -> Dict[str, int]:
        """Get rate limit stats for a user"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        requests = self.requests.get(user_id, [])
        
        return {
            "requests_last_minute": sum(1 for t in requests if t > minute_ago),
            "requests_last_hour": sum(1 for t in requests if t > hour_ago),
            "limit_per_minute": self.max_requests_per_minute,
            "limit_per_hour": self.max_requests_per_hour
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Check rate limit for a user"""
    return rate_limiter.is_allowed(user_id)

# ============== ERROR HANDLING ==============

def safe_async_handler(func):
    """Decorator for safe async handler execution"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            # Try to send error message to user
            try:
                update = args[0] if args else kwargs.get('update')
                if update and hasattr(update, 'effective_message'):
                    await update.effective_message.reply_text(
                        "❌ Ocurrió un error. Por favor intenta de nuevo.\n"
                        "Si el problema persiste, usa /start para reiniciar."
                    )
            except:
                pass
            return None
    return wrapper

# ============== DATA MASKING FOR LOGS ==============

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data for logging"""
    if not isinstance(data, dict):
        return data
    
    masked = data.copy()
    
    def mask_recursive(obj: Any) -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key.lower() in SENSITIVE_FIELDS:
                    if isinstance(value, str) and len(value) > 4:
                        result[key] = value[:2] + "***" + value[-2:]
                    else:
                        result[key] = "***"
                else:
                    result[key] = mask_recursive(value)
            return result
        elif isinstance(obj, list):
            return [mask_recursive(item) for item in obj]
        else:
            return obj
    
    return mask_recursive(masked)

# ============== AUDIT LOGGING ==============

def log_user_action(user_id: int, action: str, details: str = ""):
    """Log user action for audit trail"""
    hashed_id = hash_identifier(str(user_id))
    logger.info(f"AUDIT: user={hashed_id} action={action} details={details}")

# ============== EXPORTS ==============

__all__ = [
    'encrypt_sensitive',
    'decrypt_sensitive',
    'encrypt_user_data',
    'decrypt_user_data',
    'validate_email',
    'validate_phone',
    'validate_date',
    'validate_name',
    'validate_text_input',
    'sanitize_input',
    'check_rate_limit',
    'safe_async_handler',
    'mask_sensitive_data',
    'log_user_action',
    'ValidationError',
    'rate_limiter'
]
