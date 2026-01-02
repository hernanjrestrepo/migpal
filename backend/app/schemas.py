"""
MigPAL Schemas
Schemas de validación Pydantic para la API
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, validator


# ==================== Enums ====================

class VisaType(str, Enum):
    """Tipos de visa soportados"""
    TOURIST = "tourist"
    WORK = "work"
    STUDENT = "student"
    BUSINESS = "business"
    FAMILY = "family"
    REFUGEE = "refugee"
    PERMANENT = "permanent"
    OTHER = "other"


class MigrationStatus(str, Enum):
    """Estados del proceso migratorio"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DOCUMENTS_REQUIRED = "documents_required"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class DocumentType(str, Enum):
    """Tipos de documentos"""
    PASSPORT = "passport"
    ID_CARD = "id_card"
    BIRTH_CERTIFICATE = "birth_certificate"
    MARRIAGE_CERTIFICATE = "marriage_certificate"
    POLICE_CLEARANCE = "police_clearance"
    MEDICAL_EXAM = "medical_exam"
    BANK_STATEMENT = "bank_statement"
    EMPLOYMENT_LETTER = "employment_letter"
    EDUCATION_CERTIFICATE = "education_certificate"
    PHOTO = "photo"
    OTHER = "other"


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Schema base para usuarios"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    nationality: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema para crear usuario"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator("password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    nationality: Optional[str] = Field(None, max_length=50)


class UserResponse(UserBase):
    """Schema de respuesta de usuario"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== Authentication Schemas ====================

class Token(BaseModel):
    """Schema de token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Datos contenidos en el token"""
    user_id: str
    email: str
    exp: datetime


class LoginRequest(BaseModel):
    """Schema de request de login"""
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    """Schema para reset de contraseña"""
    email: EmailStr


class PasswordChange(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== Migration Assessment Schemas ====================

class AssessmentQuestion(BaseModel):
    """Pregunta de evaluación"""
    id: str
    question: str
    options: Optional[List[str]] = None
    required: bool = True


class AssessmentAnswer(BaseModel):
    """Respuesta a pregunta de evaluación"""
    question_id: str
    answer: str


class AssessmentRequest(BaseModel):
    """Request de evaluación migratoria"""
    destination_country: str = Field(..., min_length=2, max_length=50)
    visa_type: VisaType
    answers: List[AssessmentAnswer]


class AssessmentResult(BaseModel):
    """Resultado de evaluación migratoria"""
    id: str
    user_id: str
    destination_country: str
    visa_type: VisaType
    eligibility_score: float = Field(..., ge=0, le=100)
    recommendations: List[str]
    required_documents: List[str]
    estimated_processing_time: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Migration Process Schemas ====================

class MigrationProcessCreate(BaseModel):
    """Schema para crear proceso migratorio"""
    destination_country: str = Field(..., min_length=2, max_length=50)
    visa_type: VisaType
    planned_departure_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)


class MigrationProcessUpdate(BaseModel):
    """Schema para actualizar proceso migratorio"""
    status: Optional[MigrationStatus] = None
    planned_departure_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)


class MigrationProcessResponse(BaseModel):
    """Schema de respuesta de proceso migratorio"""
    id: str
    user_id: str
    destination_country: str
    visa_type: VisaType
    status: MigrationStatus
    planned_departure_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    documents: List["DocumentResponse"] = []
    
    class Config:
        from_attributes = True


# ==================== Document Schemas ====================

class DocumentCreate(BaseModel):
    """Schema para crear documento"""
    document_type: DocumentType
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)


class DocumentUpdate(BaseModel):
    """Schema para actualizar documento"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_verified: Optional[bool] = None


class DocumentResponse(BaseModel):
    """Schema de respuesta de documento"""
    id: str
    process_id: str
    document_type: DocumentType
    name: str
    description: Optional[str]
    file_path: Optional[str]
    is_verified: bool
    uploaded_at: datetime
    verified_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== AI Assistant Schemas ====================

class AIQueryRequest(BaseModel):
    """Request para consulta de IA"""
    question: str = Field(..., min_length=5, max_length=1000)
    context: Optional[Dict[str, Any]] = None


class AIQueryResponse(BaseModel):
    """Respuesta de consulta de IA"""
    answer: str
    confidence: float = Field(..., ge=0, le=1)
    sources: Optional[List[str]] = None
    model: str
    tokens_used: Optional[int] = None


class AIRecommendationRequest(BaseModel):
    """Request para recomendaciones de IA"""
    user_profile: Dict[str, Any]
    destination_country: str
    visa_type: VisaType


class AIRecommendationResponse(BaseModel):
    """Respuesta de recomendaciones de IA"""
    recommendations: List[str]
    action_items: List[str]
    estimated_timeline: str
    success_probability: float = Field(..., ge=0, le=1)
    model: str


# ==================== Country Information Schemas ====================

class CountryInfo(BaseModel):
    """Información de país"""
    code: str = Field(..., min_length=2, max_length=3)
    name: str
    visa_required: bool
    visa_types_available: List[VisaType]
    processing_time_days: int
    requirements: List[str]
    embassy_info: Optional[Dict[str, str]] = None


class CountryListResponse(BaseModel):
    """Lista de países"""
    countries: List[CountryInfo]
    total: int


# ==================== Notification Schemas ====================

class NotificationCreate(BaseModel):
    """Schema para crear notificación"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    notification_type: str = Field(..., max_length=50)


class NotificationResponse(BaseModel):
    """Schema de respuesta de notificación"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== Pagination Schemas ====================

class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Schema de respuesta de error"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema de error de validación"""
    error: str = "Validation Error"
    detail: List[Dict[str, Any]]


# ==================== Health Check Schemas ====================

class HealthCheckResponse(BaseModel):
    """Schema de health check"""
    status: str
    version: str
    database: str
    ai_service: str
    timestamp: datetime


# Actualizar forward references
MigrationProcessResponse.model_rebuild()
