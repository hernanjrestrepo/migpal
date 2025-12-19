
import asyncio
import sys
from pathlib import Path

# Add the project root to the python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlmodel import Session, SQLModel
from sqlalchemy import text

from app.db.session import engine
from app.models.referral_level import ReferralLevel


def populate_referral_levels():
    """
    Populates the referral_levels table with initial data.
    """
    levels = [
        {"id": 1, "name": "Level 1", "commission_rate": 0.0},
        {"id": 2, "name": "Level 2", "commission_rate": 0.01},
        {"id": 3, "name": "Level 3", "commission_rate": 0.02},
        {"id": 4, "name": "Level 4", "commission_rate": 0.03},
        {"id": 5, "name": "Level 5", "commission_rate": 0.04},
    ]

    with Session(engine) as session:
        session.exec(text("DELETE FROM referral_levels"))
        for level_data in levels:
            level = ReferralLevel(**level_data)
            session.add(level)
        session.commit()


if __name__ == "__main__":
    populate_referral_levels()
