"""
Tests para MigPAL Schemas
Pruebas de validación de schemas Pydantic
"""

import pytest
from datetime import datetime, date
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.schemas import (
    UserCreate, UserUpdate, UserResponse,
    LoginRequest, Token, PasswordChange,
    AssessmentRequest, AssessmentAnswer, AssessmentResult,
    MigrationProcessCreate, MigrationProcessUpdate, MigrationProcessResponse,
    DocumentCreate, DocumentResponse,
    AIQueryRequest, AIQueryResponse,
    VisaType, MigrationStatus, DocumentType,
    PaginationParams, ErrorResponse, HealthCheckResponse,
)


class TestUserSchemas:
    """Tests para schemas de usuario"""
    
    def test_user_create_valid(self):
        """Test creación de usuario válido"""
        user = UserCreate(
            email="test@example.com",
            full_name="John Doe",
            password="Password123"
        )
        assert user.email == "test@example.com"
        assert user.full_name == "John Doe"
    
    def test_user_create_invalid_email(self):
        """Test email inválido"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                full_name="John Doe",
                password="Password123"
            )
    
    def test_user_create_password_no_uppercase(self):
        """Test contraseña sin mayúsculas"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                full_name="John Doe",
                password="password123"
            )
        assert "uppercase" in str(exc_info.value).lower()
    
    def test_user_create_password_no_lowercase(self):
        """Test contraseña sin minúsculas"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                full_name="John Doe",
                password="PASSWORD123"
            )
        assert "lowercase" in str(exc_info.value).lower()
    
    def test_user_create_password_no_digit(self):
        """Test contraseña sin dígitos"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                full_name="John Doe",
                password="PasswordABC"
            )
        assert "digit" in str(exc_info.value).lower()
    
    def test_user_create_password_too_short(self):
        """Test contraseña muy corta"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                full_name="John Doe",
                password="Pass1"
            )
    
    def test_user_update_partial(self):
        """Test actualización parcial de usuario"""
        update = UserUpdate(full_name="Jane Doe")
        assert update.full_name == "Jane Doe"
        assert update.phone is None
    
    def test_user_response(self):
        """Test respuesta de usuario"""
        response = UserResponse(
            id="123",
            email="test@example.com",
            full_name="John Doe",
            is_active=True,
            created_at=datetime.now()
        )
        assert response.id == "123"
        assert response.is_active == True


class TestAuthSchemas:
    """Tests para schemas de autenticación"""
    
    def test_login_request(self):
        """Test request de login"""
        login = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert login.email == "test@example.com"
    
    def test_token(self):
        """Test schema de token"""
        token = Token(
            access_token="eyJ...",
            expires_in=3600
        )
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
    
    def test_password_change(self):
        """Test cambio de contraseña"""
        change = PasswordChange(
            current_password="OldPass123",
            new_password="NewPass456"
        )
        assert change.current_password == "OldPass123"


class TestAssessmentSchemas:
    """Tests para schemas de evaluación"""
    
    def test_assessment_request(self):
        """Test request de evaluación"""
        request = AssessmentRequest(
            destination_country="Canada",
            visa_type=VisaType.WORK,
            answers=[
                AssessmentAnswer(question_id="q1", answer="Yes"),
                AssessmentAnswer(question_id="q2", answer="5 years"),
            ]
        )
        assert request.destination_country == "Canada"
        assert request.visa_type == VisaType.WORK
        assert len(request.answers) == 2
    
    def test_assessment_result(self):
        """Test resultado de evaluación"""
        result = AssessmentResult(
            id="123",
            user_id="456",
            destination_country="Canada",
            visa_type=VisaType.WORK,
            eligibility_score=85.5,
            recommendations=["Apply for Express Entry"],
            required_documents=["Passport", "IELTS"],
            estimated_processing_time="6-8 months",
            created_at=datetime.now()
        )
        assert result.eligibility_score == 85.5
        assert len(result.recommendations) == 1
    
    def test_assessment_result_invalid_score(self):
        """Test score fuera de rango"""
        with pytest.raises(ValidationError):
            AssessmentResult(
                id="123",
                user_id="456",
                destination_country="Canada",
                visa_type=VisaType.WORK,
                eligibility_score=150,  # > 100
                recommendations=[],
                required_documents=[],
                estimated_processing_time="6 months",
                created_at=datetime.now()
            )


class TestMigrationProcessSchemas:
    """Tests para schemas de proceso migratorio"""
    
    def test_migration_process_create(self):
        """Test creación de proceso"""
        process = MigrationProcessCreate(
            destination_country="Australia",
            visa_type=VisaType.STUDENT,
            planned_departure_date=date(2025, 6, 1),
            notes="Planning to study MBA"
        )
        assert process.destination_country == "Australia"
        assert process.visa_type == VisaType.STUDENT
    
    def test_migration_process_update(self):
        """Test actualización de proceso"""
        update = MigrationProcessUpdate(
            status=MigrationStatus.APPROVED
        )
        assert update.status == MigrationStatus.APPROVED
    
    def test_migration_status_enum(self):
        """Test enum de estados"""
        assert MigrationStatus.PENDING == "pending"
        assert MigrationStatus.APPROVED == "approved"
        assert MigrationStatus.REJECTED == "rejected"


class TestDocumentSchemas:
    """Tests para schemas de documentos"""
    
    def test_document_create(self):
        """Test creación de documento"""
        doc = DocumentCreate(
            document_type=DocumentType.PASSPORT,
            name="Passport - John Doe",
            description="Valid until 2030"
        )
        assert doc.document_type == DocumentType.PASSPORT
        assert doc.name == "Passport - John Doe"
    
    def test_document_type_enum(self):
        """Test enum de tipos de documento"""
        assert DocumentType.PASSPORT == "passport"
        assert DocumentType.BIRTH_CERTIFICATE == "birth_certificate"
        assert DocumentType.POLICE_CLEARANCE == "police_clearance"


class TestAISchemas:
    """Tests para schemas de IA"""
    
    def test_ai_query_request(self):
        """Test request de consulta IA"""
        query = AIQueryRequest(
            question="What documents do I need for a Canadian work visa?",
            context={"country": "Canada", "visa_type": "work"}
        )
        assert len(query.question) > 5
    
    def test_ai_query_request_too_short(self):
        """Test pregunta muy corta"""
        with pytest.raises(ValidationError):
            AIQueryRequest(question="Hi")
    
    def test_ai_query_response(self):
        """Test respuesta de IA"""
        response = AIQueryResponse(
            answer="You need a passport, job offer letter...",
            confidence=0.95,
            sources=["IRCC website"],
            model="migpal",
            tokens_used=150
        )
        assert response.confidence == 0.95
        assert response.model == "migpal"
    
    def test_ai_query_response_invalid_confidence(self):
        """Test confianza fuera de rango"""
        with pytest.raises(ValidationError):
            AIQueryResponse(
                answer="Test",
                confidence=1.5,  # > 1
                model="migpal"
            )


class TestVisaTypeEnum:
    """Tests para enum de tipos de visa"""
    
    def test_all_visa_types(self):
        """Test todos los tipos de visa"""
        visa_types = [
            VisaType.TOURIST,
            VisaType.WORK,
            VisaType.STUDENT,
            VisaType.BUSINESS,
            VisaType.FAMILY,
            VisaType.REFUGEE,
            VisaType.PERMANENT,
            VisaType.OTHER,
        ]
        assert len(visa_types) == 8
    
    def test_visa_type_values(self):
        """Test valores de tipos de visa"""
        assert VisaType.TOURIST.value == "tourist"
        assert VisaType.WORK.value == "work"
        assert VisaType.STUDENT.value == "student"


class TestPaginationSchemas:
    """Tests para schemas de paginación"""
    
    def test_pagination_defaults(self):
        """Test valores por defecto"""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
    
    def test_pagination_custom(self):
        """Test valores personalizados"""
        params = PaginationParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50
    
    def test_pagination_invalid_page(self):
        """Test página inválida"""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)
    
    def test_pagination_page_size_too_large(self):
        """Test tamaño de página muy grande"""
        with pytest.raises(ValidationError):
            PaginationParams(page_size=200)


class TestErrorSchemas:
    """Tests para schemas de error"""
    
    def test_error_response(self):
        """Test respuesta de error"""
        error = ErrorResponse(
            error="Not Found",
            detail="User not found",
            code="USER_NOT_FOUND"
        )
        assert error.error == "Not Found"
        assert error.code == "USER_NOT_FOUND"


class TestHealthCheckSchema:
    """Tests para schema de health check"""
    
    def test_health_check_response(self):
        """Test respuesta de health check"""
        health = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            database="connected",
            ai_service="available",
            timestamp=datetime.now()
        )
        assert health.status == "healthy"
        assert health.database == "connected"
