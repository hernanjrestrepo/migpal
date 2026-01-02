"""
MigPAL Logging Configuration
Configuración de logging estructurado para la aplicación
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatter que produce logs en formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Agregar información extra si existe
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info[2] else None,
            }
        
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para desarrollo"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    app_name: str = "migpal"
) -> logging.Logger:
    """
    Configura el sistema de logging
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta al archivo de log (opcional)
        json_format: Si True, usa formato JSON
        app_name: Nombre de la aplicación para el logger
    
    Returns:
        Logger configurado
    """
    # Crear logger principal
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Formato base
    base_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter(base_format, date_format))
    
    logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(base_format, date_format))
        
        logger.addHandler(file_handler)
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter para agregar contexto extra a los logs"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str, **context) -> LoggerAdapter:
    """
    Obtiene un logger con contexto adicional
    
    Args:
        name: Nombre del logger
        **context: Contexto adicional para incluir en los logs
    
    Returns:
        LoggerAdapter con el contexto configurado
    """
    logger = logging.getLogger(f"migpal.{name}")
    return LoggerAdapter(logger, context)


# Loggers pre-configurados
def get_api_logger() -> LoggerAdapter:
    """Logger para endpoints de API"""
    return get_logger("api")


def get_db_logger() -> LoggerAdapter:
    """Logger para operaciones de base de datos"""
    return get_logger("database")


def get_ai_logger() -> LoggerAdapter:
    """Logger para operaciones de IA"""
    return get_logger("ai")


def get_auth_logger() -> LoggerAdapter:
    """Logger para autenticación"""
    return get_logger("auth")


def get_migration_logger() -> LoggerAdapter:
    """Logger para procesos de migración"""
    return get_logger("migration")


# Funciones helper para logging estructurado
def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None
) -> None:
    """Log de request de API"""
    logger.info(
        f"API {method} {path} -> {status_code} ({duration_ms:.2f}ms)",
        extra={
            "extra_data": {
                "type": "api_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
            }
        }
    )


def log_ai_operation(
    logger: logging.Logger,
    operation: str,
    model: str,
    duration_ms: float,
    tokens_used: Optional[int] = None,
    success: bool = True
) -> None:
    """Log de operación de IA"""
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"AI {operation} with {model} ({duration_ms:.2f}ms)",
        extra={
            "extra_data": {
                "type": "ai_operation",
                "operation": operation,
                "model": model,
                "duration_ms": duration_ms,
                "tokens_used": tokens_used,
                "success": success,
            }
        }
    )


def log_auth_event(
    logger: logging.Logger,
    event: str,
    user_id: Optional[str] = None,
    success: bool = True,
    reason: Optional[str] = None
) -> None:
    """Log de evento de autenticación"""
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        f"Auth {event}: {'success' if success else 'failed'}",
        extra={
            "extra_data": {
                "type": "auth_event",
                "event": event,
                "user_id": user_id,
                "success": success,
                "reason": reason,
            }
        }
    )


def log_migration_event(
    logger: logging.Logger,
    event: str,
    user_id: str,
    country: str,
    visa_type: Optional[str] = None,
    status: str = "in_progress"
) -> None:
    """Log de evento de proceso migratorio"""
    logger.info(
        f"Migration {event} for user {user_id} to {country}",
        extra={
            "extra_data": {
                "type": "migration_event",
                "event": event,
                "user_id": user_id,
                "country": country,
                "visa_type": visa_type,
                "status": status,
            }
        }
    )


# Inicialización por defecto
import os

_default_logger = setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE"),
    json_format=os.getenv("LOG_FORMAT", "").lower() == "json",
)
