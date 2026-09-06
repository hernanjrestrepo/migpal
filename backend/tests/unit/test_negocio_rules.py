"""Negocio — domain rules (Sprint 10, Hito 5). Funciones puras, sin red ni DB."""

import pytest

from core.negocio.domain.rules import (
    NegocioInvariantError,
    generate_service_credentials,
    validate_can_connect,
)


def test_validate_can_connect_allows_first_connection():
    validate_can_connect(already_connected=False)  # no debe lanzar


def test_validate_can_connect_raises_if_already_connected():
    with pytest.raises(NegocioInvariantError):
        validate_can_connect(already_connected=True)


def test_generate_service_credentials_email_is_deterministic_per_case():
    email_a, _ = generate_service_credentials(5)
    email_b, _ = generate_service_credentials(5)
    assert email_a == email_b == "migpal-case-5@migpal.internal"


def test_generate_service_credentials_password_is_random_each_call():
    _, password_a = generate_service_credentials(5)
    _, password_b = generate_service_credentials(5)
    assert password_a != password_b
    assert len(password_a) == 24


def test_generate_service_credentials_different_cases_get_different_emails():
    email_5, _ = generate_service_credentials(5)
    email_6, _ = generate_service_credentials(6)
    assert email_5 != email_6
