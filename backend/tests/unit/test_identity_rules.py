"""
Identity — reglas de tokens de verificación y recuperación.

Funciones puras, sin DB. Lo que se prueba acá no es "que el código corra":
son las propiedades de seguridad de las que depende que nadie pueda tomar
una cuenta ajena.
"""

from datetime import UTC, datetime, timedelta

import pytest

from core.identity.domain.rules import (
    EMAIL_VERIFICATION_TTL,
    PASSWORD_RESET_TTL,
    WeakPasswordError,
    generate_token,
    hash_token,
    is_expired,
    reset_expiry,
    validate_password,
    verification_expiry,
)

# ------------------------------------------------------------------ tokens


def test_el_token_en_claro_nunca_es_igual_al_que_se_guarda():
    """La propiedad central: lo que viaja al email y lo que queda en la base
    son cosas distintas. Si esto se rompiera, la base pasaría a contener
    credenciales reutilizables."""
    raw, stored = generate_token()
    assert raw != stored
    assert stored == hash_token(raw)


def test_dos_tokens_seguidos_nunca_coinciden():
    assert generate_token()[0] != generate_token()[0]


def test_el_token_tiene_entropia_suficiente():
    """32 bytes url-safe ≈ 43 caracteres. Un token corto sería adivinable
    por fuerza bruta contra el endpoint de reset."""
    raw, _ = generate_token()
    assert len(raw) >= 40


def test_el_hash_es_estable():
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("abd")


def test_del_hash_no_se_puede_volver_al_token():
    """No es una demostración criptográfica, es una salvaguarda contra que
    alguien reemplace el hash por algo reversible (base64, por ejemplo)."""
    raw, stored = generate_token()
    assert raw not in stored
    assert len(stored) == 64  # SHA-256 en hexadecimal


# -------------------------------------------------------------- expiración


def test_un_token_sin_fecha_de_expiracion_se_considera_expirado():
    """Ante un estado incompleto se deniega, no se concede. Si `None`
    contara como 'no expira', una fila a medio escribir daría acceso
    permanente."""
    assert is_expired(None) is True


def test_token_vencido_es_rechazado():
    assert is_expired(datetime.now(UTC) - timedelta(seconds=1)) is True


def test_token_vigente_es_aceptado():
    assert is_expired(datetime.now(UTC) + timedelta(minutes=5)) is False


def test_compara_bien_fechas_sin_zona_horaria():
    """SQLModel devuelve datetimes naive desde Postgres; compararlos con uno
    aware lanzaría TypeError y tumbaría el endpoint."""
    naive_futuro = (datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None)
    assert is_expired(naive_futuro) is False

    naive_pasado = (datetime.now(UTC) - timedelta(hours=1)).replace(tzinfo=None)
    assert is_expired(naive_pasado) is True


def test_la_ventana_de_recuperacion_es_mas_corta_que_la_de_verificacion():
    """El token de recuperación permite tomar el control de una cuenta; el
    de verificación solo confirma una casilla. Si esta relación se
    invirtiera, sería una regresión de seguridad."""
    assert PASSWORD_RESET_TTL < EMAIL_VERIFICATION_TTL

    ahora = datetime.now(UTC)
    assert reset_expiry(ahora) == ahora + PASSWORD_RESET_TTL
    assert verification_expiry(ahora) == ahora + EMAIL_VERIFICATION_TTL


# ------------------------------------------------------------ contraseñas


def test_rechaza_contrasenas_cortas():
    with pytest.raises(WeakPasswordError):
        validate_password("corta7")


def test_acepta_contrasenas_de_ocho_o_mas():
    validate_password("12345678")          # no debe lanzar
    validate_password("una frase larga como contraseña")
