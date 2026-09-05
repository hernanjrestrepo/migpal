"""
Envío de emails transaccionales (verificación de cuenta y recuperación de
contraseña).

Decisión central: **si SMTP no está configurado, no falla — registra el
enlace en el log y sigue.**

No es una concesión perezosa. Sin esto, el flujo completo de verificación y
recuperación sería imposible de probar en desarrollo sin credenciales SMTP
reales, que es exactamente el escenario en el que se desarrolla. El
comportamiento es explícito y ruidoso en el log, no silencioso.

En producción, `ENVIRONMENT=production` sin SMTP configurado se registra
como ERROR, no como INFO: ahí sí es un problema real que hay que ver.

Se envía en un hilo aparte (`run_in_threadpool`) porque `smtplib` es
bloqueante: llamarlo directo desde un endpoint async congelaría el event
loop de todo el backend mientras dura el diálogo con el servidor SMTP.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from starlette.concurrency import run_in_threadpool

from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _send_sync(to: str, subject: str, text_body: str, html_body: str) -> bool:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info(f"Email enviado a {to}: {subject}")
        return True
    except Exception as exc:  # noqa: BLE001 -- un fallo de email no debe tumbar el request
        logger.error(f"No se pudo enviar el email a {to} ({subject}): {exc}")
        return False


async def send_email(*, to: str, subject: str, text_body: str, html_body: str, link: str) -> bool:
    """Devuelve True si el email salió de verdad. Nunca lanza: el caller
    decide qué hacer, y en ningún caso el usuario debe ver un 500 porque el
    servidor de correo esté caído."""

    if not _smtp_configured():
        # El enlace se registra para que el flujo sea usable en desarrollo.
        if settings.environment == "production":
            logger.error(
                f"SMTP NO CONFIGURADO en producción: el email '{subject}' para {to} no se envió. "
                f"Configurá SMTP_HOST/SMTP_USER/SMTP_PASSWORD."
            )
        else:
            logger.warning(
                f"[SMTP no configurado] Email '{subject}' para {to} NO enviado. "
                f"Enlace para probar el flujo manualmente: {link}"
            )
        return False

    return await run_in_threadpool(_send_sync, to, subject, text_body, html_body)


# ---------------------------------------------------------------- plantillas

_BASE_STYLE = (
    "font-family:-apple-system,'Segoe UI',Roboto,sans-serif;"
    "max-width:520px;margin:0 auto;padding:32px 24px;color:#0f172a;line-height:1.6"
)
_BUTTON_STYLE = (
    "display:inline-block;background:#2454eb;color:#ffffff;text-decoration:none;"
    "padding:12px 24px;border-radius:8px;font-weight:600;margin:20px 0"
)


def _wrap(title: str, body_html: str, link: str, button_label: str) -> str:
    return f"""<div style="{_BASE_STYLE}">
  <div style="font-size:18px;font-weight:800;letter-spacing:-.02em;margin-bottom:24px">MigPAL</div>
  <h1 style="font-size:20px;margin:0 0 12px">{title}</h1>
  {body_html}
  <a href="{link}" style="{_BUTTON_STYLE}">{button_label}</a>
  <p style="font-size:13px;color:#64748b">
    Si el botón no funciona, copiá y pegá este enlace en tu navegador:<br>
    <span style="word-break:break-all">{link}</span>
  </p>
  <hr style="border:none;border-top:1px solid #e5e9f0;margin:28px 0">
  <p style="font-size:12px;color:#94a3b8">
    MigPAL es una herramienta de orientación migratoria y no constituye
    asesoría legal.
  </p>
</div>"""


def verification_email(link: str) -> tuple[str, str, str]:
    """Devuelve `(asunto, cuerpo_texto, cuerpo_html)`."""
    subject = "Confirmá tu cuenta de MigPAL"
    text = (
        "Bienvenido a MigPAL.\n\n"
        "Confirmá tu dirección de email para activar tu cuenta:\n"
        f"{link}\n\n"
        "El enlace vence en 24 horas.\n\n"
        "Si no creaste esta cuenta, podés ignorar este mensaje."
    )
    html = _wrap(
        "Confirmá tu cuenta",
        "<p>Ya casi estás. Confirmá tu dirección de email para activar tu cuenta "
        "y empezar tu evaluación migratoria.</p>"
        "<p style='font-size:13px;color:#64748b'>El enlace vence en 24 horas.</p>",
        link,
        "Confirmar mi cuenta",
    )
    return subject, text, html


def password_reset_email(link: str) -> tuple[str, str, str]:
    subject = "Restablecer tu contraseña de MigPAL"
    text = (
        "Recibimos un pedido para restablecer tu contraseña.\n\n"
        f"Creá una contraseña nueva acá:\n{link}\n\n"
        "El enlace vence en 1 hora y solo se puede usar una vez.\n\n"
        "Si no pediste esto, ignorá este mensaje: tu contraseña actual sigue siendo válida."
    )
    html = _wrap(
        "Restablecer tu contraseña",
        "<p>Recibimos un pedido para restablecer la contraseña de tu cuenta.</p>"
        "<p style='font-size:13px;color:#64748b'>El enlace vence en 1 hora y solo "
        "se puede usar una vez.</p>"
        "<p style='font-size:13px;color:#64748b'>Si no pediste esto, ignorá este "
        "mensaje: tu contraseña actual sigue siendo válida.</p>",
        link,
        "Crear contraseña nueva",
    )
    return subject, text, html
