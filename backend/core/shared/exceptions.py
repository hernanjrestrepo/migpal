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


class RecommendationNotFound(DomainError):
    """No existe, o no pertenece al caso del usuario autenticado -- ver
    core/recommendation/application/handlers.py. No es una invariante de
    Recommendation en sí (eso vive en domain/rules.py), es una regla de
    acceso/consulta (misma categoría que CaseNotFound)."""


class ExecutionPlanNotFound(DomainError):
    """No existe, o no pertenece al caso del usuario autenticado -- ver
    core/execution_plan/application/handlers.py. Misma categoría que
    RecommendationNotFound: regla de acceso/consulta, no una invariante del
    aggregate (eso vive en core/execution_plan/domain/rules.py)."""


class SettlementNotFound(DomainError):
    """No existe, o no pertenece al caso del usuario autenticado -- ver
    core/settlement/application/handlers.py. Misma categoría que
    ExecutionPlanNotFound."""


class CommunityGroupNotFound(DomainError):
    pass


class CommunityPostNotFound(DomainError):
    pass


class MarketplaceListingNotFound(DomainError):
    pass


class MarketplaceTransactionNotFound(DomainError):
    """No existe, o no pertenece (ni como comprador ni como vendedor) al
    usuario autenticado -- ver core/marketplace/application/handlers.py."""
