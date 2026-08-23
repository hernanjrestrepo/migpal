from datetime import datetime

from sqlmodel import Field, SQLModel


class UserMigrationProfile(SQLModel, table=True):
    """
    User's migration profile with personal information for assessment
    """

    __tablename__ = "user_migration_profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)

    # Origin and destination
    current_country: str
    target_country: str

    # Personal information
    age: int | None = None
    education_level: str  # "high_school", "bachelor", "master", "phd"
    work_experience_years: int = 0
    occupation: str | None = None
    language_skills: str  # JSON string with languages and proficiency levels

    # Family status
    family_status: str  # "single", "married", "married_with_children"
    dependents: int = 0

    # Financial
    budget_usd: float = 0.0

    # Migration preferences
    urgency: str = Field(default="medium")  # "low", "medium", "high"
    selected_process_id: int | None = Field(default=None, foreign_key="migration_processes.id")
    current_stage: str = Field(
        default="assessment"
    )  # "assessment", "preparation", "application", "waiting", "approved", "rejected"

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserMigrationProfileCreate(SQLModel):
    current_country: str
    target_country: str
    age: int | None = None
    education_level: str
    work_experience_years: int = 0
    occupation: str | None = None
    language_skills: str
    family_status: str
    dependents: int = 0
    budget_usd: float = 0.0
    urgency: str = "medium"


class UserMigrationProfileRead(SQLModel):
    id: int
    user_id: int
    current_country: str
    target_country: str
    age: int | None
    education_level: str
    work_experience_years: int
    occupation: str | None
    language_skills: str
    family_status: str
    dependents: int
    budget_usd: float
    urgency: str
    selected_process_id: int | None
    current_stage: str
    created_at: datetime
    updated_at: datetime


class UserMigrationProfileUpdate(SQLModel):
    current_country: str | None = None
    target_country: str | None = None
    age: int | None = None
    education_level: str | None = None
    work_experience_years: int | None = None
    occupation: str | None = None
    language_skills: str | None = None
    family_status: str | None = None
    dependents: int | None = None
    budget_usd: float | None = None
    urgency: str | None = None
    selected_process_id: int | None = None
    current_stage: str | None = None
