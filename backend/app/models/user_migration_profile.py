from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class UserMigrationProfile(SQLModel, table=True):
    """
    User's migration profile with personal information for assessment
    """
    __tablename__ = "user_migration_profiles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    
    # Origin and destination
    current_country: str
    target_country: str
    
    # Personal information
    age: Optional[int] = None
    education_level: str  # "high_school", "bachelor", "master", "phd"
    work_experience_years: int = 0
    occupation: Optional[str] = None
    language_skills: str  # JSON string with languages and proficiency levels
    
    # Family status
    family_status: str  # "single", "married", "married_with_children"
    dependents: int = 0
    
    # Financial
    budget_usd: float = 0.0
    
    # Migration preferences
    urgency: str = Field(default="medium")  # "low", "medium", "high"
    selected_process_id: Optional[int] = Field(default=None, foreign_key="migration_processes.id")
    current_stage: str = Field(default="assessment")  # "assessment", "preparation", "application", "waiting", "approved", "rejected"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserMigrationProfileCreate(SQLModel):
    current_country: str
    target_country: str
    age: Optional[int] = None
    education_level: str
    work_experience_years: int = 0
    occupation: Optional[str] = None
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
    age: Optional[int]
    education_level: str
    work_experience_years: int
    occupation: Optional[str]
    language_skills: str
    family_status: str
    dependents: int
    budget_usd: float
    urgency: str
    selected_process_id: Optional[int]
    current_stage: str
    created_at: datetime
    updated_at: datetime


class UserMigrationProfileUpdate(SQLModel):
    current_country: Optional[str] = None
    target_country: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None
    work_experience_years: Optional[int] = None
    occupation: Optional[str] = None
    language_skills: Optional[str] = None
    family_status: Optional[str] = None
    dependents: Optional[int] = None
    budget_usd: Optional[float] = None
    urgency: Optional[str] = None
    selected_process_id: Optional[int] = None
    current_stage: Optional[str] = None
