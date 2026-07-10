"""Excepciones de dominio compartidas entre bounded contexts."""


class DomainError(Exception):
    """Base de toda excepción de dominio -- nunca se lanza directamente."""


class InvalidCaseTransition(DomainError):
    """MigrationCase: se intentó una transición de estado no permitida.

    Ver Anexo A -- invariante de MigrationCase: el aggregate solo acepta
    comandos de transición explícitos, nunca lógica de negocio ad-hoc.
    """


class CaseNotFound(DomainError):
    pass


class IdentityAlreadyExists(DomainError):
    pass
