"""
MigPAL Database Module
Base de datos SQLite para mentores, abogados, empleos y usuarios
"""

import aiosqlite
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "migpal.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ============== DATABASE INITIALIZATION ==============

async def init_database():
    """Initialize database with all tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                telegram_name TEXT,
                language TEXT DEFAULT 'en',
                profile_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notifications_enabled INTEGER DEFAULT 1,
                last_notification TIMESTAMP
            )
        """)
        
        # Mentors table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mentors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country_origin TEXT,
                country_destination TEXT,
                visa_type TEXT,
                profession TEXT,
                year_migrated INTEGER,
                languages TEXT,
                specialties TEXT,
                rating REAL DEFAULT 5.0,
                sessions INTEGER DEFAULT 0,
                bio TEXT,
                contact TEXT,
                available INTEGER DEFAULT 1,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Lawyers table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lawyers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT,
                specialties TEXT,
                languages TEXT,
                firm TEXT,
                location TEXT,
                consultation_fee REAL,
                rating REAL DEFAULT 5.0,
                reviews INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 1,
                contact TEXT,
                website TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Jobs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                country TEXT,
                visa_sponsorship INTEGER DEFAULT 1,
                visa_types TEXT,
                salary TEXT,
                requirements TEXT,
                description TEXT,
                url TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                active INTEGER DEFAULT 1
            )
        """)
        
        # Notifications table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                message TEXT,
                scheduled_at TIMESTAMP,
                sent_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # User documents tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                document_name TEXT,
                document_type TEXT,
                status TEXT DEFAULT 'pending',
                expires_at TIMESTAMP,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        await db.commit()
        logger.info("Database initialized successfully")
        
        # Insert sample data if empty
        await _insert_sample_data(db)

async def _insert_sample_data(db):
    """Insert sample mentors, lawyers, and jobs if tables are empty"""
    
    # Check if mentors exist
    cursor = await db.execute("SELECT COUNT(*) FROM mentors")
    count = (await cursor.fetchone())[0]
    
    if count == 0:
        # Insert sample mentors
        mentors = [
            ("María González", "Colombia", "USA", "H-1B", "Software Engineer", 2020, 
             '["Spanish", "English"]', '["Tech", "H-1B", "Silicon Valley"]', 4.9, 45,
             "Migrated with H-1B to work at Google. Happy to help other tech workers.", 
             "@maria_mentor", 1, 1),
            ("Carlos Rodríguez", "Venezuela", "Canada", "Express Entry", "Accountant", 2019,
             '["Spanish", "English", "French"]', '["Express Entry", "Toronto", "Finance"]', 4.8, 62,
             "PR in Canada via Express Entry. Specialist in the process for finance professionals.",
             "@carlos_mentor", 1, 1),
            ("Ana Martínez", "Mexico", "Spain", "Digital Nomad", "UX Designer", 2022,
             '["Spanish", "English"]', '["Digital Nomad", "Freelance", "Barcelona"]', 4.7, 28,
             "Remote work from Barcelona. Expert in digital nomad visa.",
             "@ana_mentor", 1, 1),
            ("Pedro Sánchez", "Argentina", "Germany", "Blue Card", "Mechanical Engineer", 2021,
             '["Spanish", "English", "German"]', '["Blue Card", "Engineering", "Munich"]', 4.9, 33,
             "Blue Card in Germany. I especially help engineers and technicians.",
             "@pedro_mentor", 1, 1),
            ("Laura Pérez", "Peru", "USA", "F-1 → H-1B", "Data Scientist", 2018,
             '["Spanish", "English"]', '["Student", "OPT", "STEM"]', 4.8, 51,
             "Came as F-1 student, now have H-1B. I know the academic route well.",
             "@laura_mentor", 1, 1),
            ("Ahmed Hassan", "Egypt", "Canada", "Express Entry", "Civil Engineer", 2020,
             '["Arabic", "English"]', '["Express Entry", "Engineering", "Ontario"]', 4.7, 38,
             "Migrated from Cairo to Toronto. Helping MENA region migrants.",
             "@ahmed_mentor", 1, 1),
            ("Priya Sharma", "India", "USA", "H-1B", "Product Manager", 2019,
             '["Hindi", "English"]', '["H-1B", "Tech", "Bay Area"]', 4.9, 67,
             "From Bangalore to San Francisco. Expert in tech immigration.",
             "@priya_mentor", 1, 1),
            ("Wei Chen", "China", "Australia", "Skilled Worker", "Software Developer", 2021,
             '["Chinese", "English"]', '["Australia", "Tech", "Sydney"]', 4.6, 29,
             "Migrated to Sydney. Helping Chinese tech workers move to Australia.",
             "@wei_mentor", 1, 1),
            ("Olga Petrova", "Ukraine", "Germany", "Job Seeker", "Marketing Manager", 2022,
             '["Ukrainian", "Russian", "English", "German"]', '["Germany", "Marketing", "Berlin"]', 4.8, 41,
             "Relocated to Berlin. Specialist in German job market for Eastern Europeans.",
             "@olga_mentor", 1, 1),
            ("Kenji Tanaka", "Japan", "USA", "L-1", "Business Analyst", 2020,
             '["Japanese", "English"]', '["L-1", "Intracompany", "New York"]', 4.7, 22,
             "Transferred from Tokyo to NYC. Expert in intracompany transfers.",
             "@kenji_mentor", 1, 1),
        ]
        
        await db.executemany("""
            INSERT INTO mentors (name, country_origin, country_destination, visa_type, 
                profession, year_migrated, languages, specialties, rating, sessions, 
                bio, contact, available, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, mentors)
        
        # Insert sample lawyers
        lawyers = [
            ("Lic. Roberto Fernández", "USA", '["H-1B", "Green Card", "Asylum"]',
             '["Spanish", "English"]', "Fernández Immigration Law", "Miami, FL",
             150, 4.8, 127, 1, "rfernandez@immigration.com", "https://fernandezlaw.com"),
            ("Abg. Patricia Morales", "Canada", '["Express Entry", "PNP", "Refugee"]',
             '["Spanish", "English", "French"]', "Morales & Associates", "Toronto, ON",
             100, 4.9, 89, 1, "pmorales@canadaimmigration.ca", "https://moraleslaw.ca"),
            ("Abg. Juan García", "Spain", '["Work Visa", "Student", "Arraigo"]',
             '["Spanish"]', "García Extranjería", "Madrid",
             80, 4.7, 156, 1, "jgarcia@extranjeria.es", "https://garciaextranjeria.es"),
            ("RA Michael Schmidt", "Germany", '["Blue Card", "Work", "Family"]',
             '["Spanish", "English", "German"]', "Schmidt Rechtsanwälte", "Berlin",
             120, 4.6, 67, 1, "mschmidt@immigration-de.com", "https://schmidt-law.de"),
            ("Atty. Sarah Johnson", "USA", '["EB-1", "EB-2", "O-1"]',
             '["English"]', "Johnson Immigration Group", "New York, NY",
             200, 4.9, 203, 1, "sjohnson@jiglaw.com", "https://johnsonimmigration.com"),
            ("Avv. Marco Rossi", "Italy", '["Work", "Student", "EU Blue Card"]',
             '["Italian", "English"]', "Studio Legale Rossi", "Milan",
             90, 4.5, 78, 1, "mrossi@studiorossi.it", "https://studiorossi.it"),
            ("Adv. Raj Patel", "UK", '["Skilled Worker", "Student", "Family"]',
             '["English", "Hindi", "Gujarati"]', "Patel Immigration Solicitors", "London",
             130, 4.8, 145, 1, "raj@patelimmigration.co.uk", "https://patelimmigration.co.uk"),
            ("弁護士 Yuki Yamamoto", "Japan", '["Work", "Business", "Investor"]',
             '["Japanese", "English"]', "Yamamoto Legal Office", "Tokyo",
             180, 4.7, 56, 1, "yuki@yamamoto-legal.jp", "https://yamamoto-legal.jp"),
        ]
        
        await db.executemany("""
            INSERT INTO lawyers (name, country, specialties, languages, firm, location,
                consultation_fee, rating, reviews, verified, contact, website)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lawyers)
        
        # Insert sample jobs
        jobs = [
            ("Software Engineer", "TechCorp Inc.", "San Francisco, USA", "USA", 1,
             '["H-1B", "L-1"]', "$120,000 - $180,000", 
             '["5+ years experience", "Python/Java", "Advanced English"]',
             "Join our engineering team building next-gen products.",
             "https://techcorp.com/careers"),
            ("Data Analyst", "DataFlow Canada", "Toronto, Canada", "Canada", 1,
             '["LMIA", "Express Entry support"]', "$80,000 - $100,000 CAD",
             '["3+ years experience", "SQL/Python", "IELTS 7+"]',
             "Analyze data to drive business decisions.",
             "https://dataflow.ca/jobs"),
            ("UX Designer", "DesignHub Barcelona", "Barcelona, Spain", "Spain", 1,
             '["Work Visa", "Digital Nomad"]', "€45,000 - €60,000",
             '["Strong portfolio", "Figma", "Spanish or English"]',
             "Design beautiful user experiences for global clients.",
             "https://designhub.es/careers"),
            ("Mechanical Engineer", "AutoTech GmbH", "Munich, Germany", "Germany", 1,
             '["Blue Card"]', "€55,000 - €75,000",
             '["Engineering degree", "CAD/CAM", "English B2+"]',
             "Work on cutting-edge automotive technology.",
             "https://autotech.de/karriere"),
            ("Registered Nurse", "HealthCare USA", "Houston, USA", "USA", 1,
             '["EB-3", "H-1B"]', "$70,000 - $90,000",
             '["Nursing license", "NCLEX passed", "English"]',
             "Join our healthcare team making a difference.",
             "https://healthcare-usa.com/nursing"),
            ("Product Manager", "StartupXYZ", "London, UK", "UK", 1,
             '["Skilled Worker"]', "£60,000 - £80,000",
             '["3+ years PM experience", "Agile", "English native"]',
             "Lead product development for our growing startup.",
             "https://startupxyz.co.uk/jobs"),
            ("DevOps Engineer", "CloudNine", "Sydney, Australia", "Australia", 1,
             '["Skilled Worker 482"]', "$100,000 - $130,000 AUD",
             '["AWS/GCP", "Kubernetes", "CI/CD"]',
             "Build and maintain cloud infrastructure.",
             "https://cloudnine.com.au/careers"),
            ("Marketing Manager", "GlobalBrand", "Amsterdam, Netherlands", "Netherlands", 1,
             '["Highly Skilled Migrant"]', "€50,000 - €70,000",
             '["5+ years marketing", "Digital marketing", "English"]',
             "Lead marketing campaigns across Europe.",
             "https://globalbrand.nl/vacatures"),
        ]
        
        await db.executemany("""
            INSERT INTO jobs (title, company, location, country, visa_sponsorship,
                visa_types, salary, requirements, description, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, jobs)
        
        await db.commit()
        logger.info("Sample data inserted successfully")

# ============== USER OPERATIONS ==============

async def save_user(user_id: int, data: Dict[str, Any]):
    """Save or update user data"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, telegram_name, language, profile_data, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                telegram_name = excluded.telegram_name,
                language = excluded.language,
                profile_data = excluded.profile_data,
                updated_at = excluded.updated_at
        """, (
            user_id,
            data.get("profile", {}).get("personal", {}).get("telegram_name"),
            data.get("language", "en"),
            json.dumps(data),
            datetime.now().isoformat()
        ))
        await db.commit()

async def get_user(user_id: int) -> Optional[Dict]:
    """Get user data"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT profile_data FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

async def get_users_for_notifications() -> List[Dict]:
    """Get users who have notifications enabled"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT user_id, language, profile_data 
            FROM users 
            WHERE notifications_enabled = 1
        """)
        rows = await cursor.fetchall()
        return [{"user_id": r[0], "language": r[1], "data": json.loads(r[2])} for r in rows]

# ============== MENTOR OPERATIONS ==============

async def get_mentors(country: str = None, limit: int = 10) -> List[Dict]:
    """Get mentors, optionally filtered by destination country"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if country:
            cursor = await db.execute("""
                SELECT * FROM mentors 
                WHERE country_destination = ? AND available = 1 AND verified = 1
                ORDER BY rating DESC, sessions DESC
                LIMIT ?
            """, (country, limit))
        else:
            cursor = await db.execute("""
                SELECT * FROM mentors 
                WHERE available = 1 AND verified = 1
                ORDER BY rating DESC, sessions DESC
                LIMIT ?
            """, (limit,))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_mentor_by_id(mentor_id: int) -> Optional[Dict]:
    """Get a specific mentor by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM mentors WHERE id = ?", (mentor_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

# ============== LAWYER OPERATIONS ==============

async def get_lawyers(country: str = None, limit: int = 10) -> List[Dict]:
    """Get lawyers, optionally filtered by country"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if country:
            cursor = await db.execute("""
                SELECT * FROM lawyers 
                WHERE country = ? AND verified = 1
                ORDER BY rating DESC, reviews DESC
                LIMIT ?
            """, (country, limit))
        else:
            cursor = await db.execute("""
                SELECT * FROM lawyers 
                WHERE verified = 1
                ORDER BY rating DESC, reviews DESC
                LIMIT ?
            """, (limit,))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# ============== JOB OPERATIONS ==============

async def get_jobs(country: str = None, limit: int = 10) -> List[Dict]:
    """Get jobs with visa sponsorship"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if country:
            cursor = await db.execute("""
                SELECT * FROM jobs 
                WHERE country = ? AND visa_sponsorship = 1 AND active = 1
                ORDER BY posted_at DESC
                LIMIT ?
            """, (country, limit))
        else:
            cursor = await db.execute("""
                SELECT * FROM jobs 
                WHERE visa_sponsorship = 1 AND active = 1
                ORDER BY posted_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# ============== NOTIFICATION OPERATIONS ==============

async def schedule_notification(user_id: int, notification_type: str, message: str, scheduled_at: datetime):
    """Schedule a notification for a user"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO notifications (user_id, type, message, scheduled_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, notification_type, message, scheduled_at.isoformat()))
        await db.commit()

async def get_pending_notifications() -> List[Dict]:
    """Get notifications that are due to be sent"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT n.*, u.language 
            FROM notifications n
            JOIN users u ON n.user_id = u.user_id
            WHERE n.status = 'pending' AND n.scheduled_at <= ?
        """, (datetime.now().isoformat(),))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def mark_notification_sent(notification_id: int):
    """Mark a notification as sent"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE notifications 
            SET status = 'sent', sent_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), notification_id))
        await db.commit()

# ============== DOCUMENT TRACKING ==============

async def add_user_document(user_id: int, doc_name: str, doc_type: str, expires_at: datetime = None):
    """Track a user's document"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_documents (user_id, document_name, document_type, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, doc_name, doc_type, expires_at.isoformat() if expires_at else None))
        await db.commit()

async def get_expiring_documents(days_ahead: int = 30) -> List[Dict]:
    """Get documents expiring within specified days"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT d.*, u.language 
            FROM user_documents d
            JOIN users u ON d.user_id = u.user_id
            WHERE d.expires_at IS NOT NULL 
            AND d.expires_at <= datetime('now', '+' || ? || ' days')
            AND d.status != 'expired_notified'
        """, (days_ahead,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
