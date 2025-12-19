# This file ensures that all models are imported and registered with SQLModel
# before they are used, which can help prevent circular import issues with relationships.

from .referral_level import ReferralLevel
from .user import User

# Rebuild models to resolve forward references, the Pydantic v2+ way
User.model_rebuild()
ReferralLevel.model_rebuild()
