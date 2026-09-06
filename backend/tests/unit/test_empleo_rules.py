"""Empleo — domain rules (Sprint 10b, Hito 5). Funciones puras, sin red ni DB."""

import pytest

from core.empleo.domain.rules import EmpleoInvariantError, generate_service_credentials, validate_can_connect


def test_validate_can_connect_allows_first_connection():
    validate_can_connect(already_connected=False)  # no debe lanzar


def test_validate_can_connect_raises_if_already_connected():
    with pytest.raises(EmpleoInvariantError):
        validate_can_connect(already_connected=True)


def test_generate_service_credentials_email_is_deterministic_per_case():
    email_a, _ = generate_service_credentials(7)
    email_b, _ = generate_service_credentials(7)
    assert email_a == email_b == "migpal-case-7@migpal.internal"


def test_generate_service_credentials_password_is_random_each_call():
    _, password_a = generate_service_credentials(7)
    _, password_b = generate_service_credentials(7)
    assert password_a != password_b
