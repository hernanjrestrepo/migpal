from datetime import datetime

from sqlmodel import Field, SQLModel


class MigrationProcess(SQLModel, table=True):
    """
    Represents a migration process/route (e.g., US H1B Visa, Canada Express Entry)
    """

    __tablename__ = "migration_processes"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # "US Work Visa H1B", "Canada Express Entry"
    country_from: str = Field(index=True)  # Origin country
    country_to: str = Field(index=True)  # Destination country
    visa_type: str = Field(index=True)  # "work", "study", "family", "asylum", "permanent_residence"
    description: str  # Detailed description
    requirements: str  # JSON string with requirements list
    estimated_cost_min: float  # Minimum cost in USD
    estimated_cost_max: float  # Maximum cost in USD
    estimated_time_months: int  # Estimated time in months
    difficulty_level: str = Field(default="medium")  # "easy", "medium", "hard"
    success_rate: float = Field(default=0.0)  # Success rate percentage (0-100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MigrationProcessCreate(SQLModel):
    name: str
    country_from: str
    country_to: str
    visa_type: str
    description: str
    requirements: str
    estimated_cost_min: float
    estimated_cost_max: float
    estimated_time_months: int
    difficulty_level: str = "medium"
    success_rate: float = 0.0


class MigrationProcessRead(SQLModel):
    id: int
    name: str
    country_from: str
    country_to: str
    visa_type: str
    description: str
    requirements: str
    estimated_cost_min: float
    estimated_cost_max: float
    estimated_time_months: int
    difficulty_level: str
    success_rate: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
