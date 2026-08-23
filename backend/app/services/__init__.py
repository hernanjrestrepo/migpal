# Imports tolerantes a fallos para evitar bloqueo por dependencias faltantes
try:
    from . import zillow  # noqa: F401
except ImportError:
    zillow = None

try:
    from . import businesses  # noqa: F401
except ImportError:
    businesses = None

try:
    from . import legal  # noqa: F401
except ImportError:
    legal = None

try:
    from . import education  # noqa: F401
except ImportError:
    education = None

try:
    from . import jobs  # noqa: F401
except ImportError:
    jobs = None

# V4.0 - MigPAL USA Standard
try:
    from . import (
        migpal_usa_integration,  # noqa: F401
        migpal_usa_standard,  # noqa: F401
        migpal_v4_middleware,  # noqa: F401
    )
except ImportError:
    migpal_usa_standard = None
    migpal_usa_integration = None
    migpal_v4_middleware = None
