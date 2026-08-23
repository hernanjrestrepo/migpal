"""
MigPAL Case Storage
Persistencia de datos de usuarios y casos migratorios
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Base directory for cases
CASES_DIR = Path(__file__).parent.parent.parent / "data" / "cases"
CASES_DIR.mkdir(parents=True, exist_ok=True)


def get_case_path(user_id: int) -> Path:
    """Get the path for a user's case folder"""
    case_dir = CASES_DIR / str(user_id)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def save_user_data(user_id: int, data: dict[str, Any]) -> bool:
    """Save user data to disk"""
    try:
        case_dir = get_case_path(user_id)

        # Update timestamp
        data["updated_at"] = datetime.now().isoformat()

        # Save main profile
        profile_path = case_dir / "profile.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved data for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving data for user {user_id}: {e}")
        return False


def load_user_data(user_id: int) -> dict[str, Any] | None:
    """Load user data from disk"""
    try:
        case_dir = get_case_path(user_id)
        profile_path = case_dir / "profile.json"

        if profile_path.exists():
            with open(profile_path, encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded data for user {user_id}")
            return data

        return None
    except Exception as e:
        logger.error(f"Error loading data for user {user_id}: {e}")
        return None


def save_conversation(user_id: int, message: str, response: str, role: str = "user"):
    """Save a conversation message"""
    try:
        case_dir = get_case_path(user_id)
        conv_path = case_dir / "conversations.json"

        # Load existing conversations
        conversations = []
        if conv_path.exists():
            with open(conv_path, encoding="utf-8") as f:
                conversations = json.load(f)

        # Add new message
        conversations.append(
            {"timestamp": datetime.now().isoformat(), "role": role, "message": message, "response": response}
        )

        # Keep last 100 messages
        if len(conversations) > 100:
            conversations = conversations[-100:]

        # Save
        with open(conv_path, "w", encoding="utf-8") as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        logger.error(f"Error saving conversation for user {user_id}: {e}")
        return False


def load_conversations(user_id: int, limit: int = 20) -> list:
    """Load recent conversations"""
    try:
        case_dir = get_case_path(user_id)
        conv_path = case_dir / "conversations.json"

        if conv_path.exists():
            with open(conv_path, encoding="utf-8") as f:
                conversations = json.load(f)
            return conversations[-limit:]

        return []
    except Exception as e:
        logger.error(f"Error loading conversations for user {user_id}: {e}")
        return []


def save_document_info(user_id: int, doc_info: dict[str, Any]) -> bool:
    """Save document information"""
    try:
        case_dir = get_case_path(user_id)
        docs_path = case_dir / "documents.json"

        # Load existing documents
        documents = []
        if docs_path.exists():
            with open(docs_path, encoding="utf-8") as f:
                documents = json.load(f)

        # Add new document
        doc_info["uploaded_at"] = datetime.now().isoformat()
        documents.append(doc_info)

        # Save
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        logger.error(f"Error saving document for user {user_id}: {e}")
        return False


def load_documents(user_id: int) -> list:
    """Load user's documents"""
    try:
        case_dir = get_case_path(user_id)
        docs_path = case_dir / "documents.json"

        if docs_path.exists():
            with open(docs_path, encoding="utf-8") as f:
                return json.load(f)

        return []
    except Exception as e:
        logger.error(f"Error loading documents for user {user_id}: {e}")
        return []


def get_user_summary(user_id: int) -> str:
    """Get a summary of user's case"""
    data = load_user_data(user_id)
    if not data:
        return "No hay datos guardados."

    profile = data.get("profile", {})
    personal = profile.get("personal", {})
    route = data.get("selected_route", {})
    state = data.get("state", "start")

    summary = f"""
📋 *Resumen del Caso*

👤 *Solicitante:* {personal.get('name', 'N/A')}
📧 Email: {personal.get('email', 'N/A')}
📱 Tel: {personal.get('phone', 'N/A')}
🎂 Nacimiento: {personal.get('birth_date', 'N/A')}
🏳️ Nacionalidad: {personal.get('nationality', 'N/A')}
📍 Ubicación: {personal.get('current_city', '')}, {personal.get('current_country', '')}

🎓 *Educación:* {profile.get('education', {}).get('level', 'N/A')} - {profile.get('education', {}).get('career', 'N/A')}
💼 *Profesión:* {profile.get('work', {}).get('profession', 'N/A')}
🌐 *Inglés:* {profile.get('languages', {}).get('english', 'N/A')}

🎯 *Destino:* {route.get('country', 'No seleccionado')}
📄 *Visa:* {route.get('visa_type', 'No seleccionada')}
🏙️ *Ciudad:* {route.get('city', 'No seleccionada')}

📊 *Estado:* {state}
📅 *Última actualización:* {data.get('updated_at', 'N/A')}
"""

    # Add family info
    family = data.get("family_members", [])
    if family:
        summary += f"\n👨‍👩‍👧‍👦 *Familia:* {len(family)} miembro(s)\n"
        for member in family:
            summary += f"  • {member.get('name', 'N/A')} ({member.get('relation', 'N/A')})\n"

    # Add documents count
    docs = load_documents(user_id)
    if docs:
        summary += f"\n📎 *Documentos:* {len(docs)} archivo(s)\n"

    return summary


def delete_user_data(user_id: int) -> bool:
    """Delete all user data (for /nuevo command)"""
    try:
        import shutil

        case_dir = get_case_path(user_id)
        if case_dir.exists():
            shutil.rmtree(case_dir)
        logger.info(f"Deleted data for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting data for user {user_id}: {e}")
        return False


def list_all_cases() -> list:
    """List all cases (for admin purposes)"""
    try:
        cases = []
        for case_dir in CASES_DIR.iterdir():
            if case_dir.is_dir():
                user_id = case_dir.name
                data = load_user_data(int(user_id))
                if data:
                    cases.append(
                        {
                            "user_id": user_id,
                            "name": data.get("profile", {}).get("personal", {}).get("name", "N/A"),
                            "state": data.get("state", "unknown"),
                            "updated_at": data.get("updated_at", "N/A"),
                        }
                    )
        return cases
    except Exception as e:
        logger.error(f"Error listing cases: {e}")
        return []
