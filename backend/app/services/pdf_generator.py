"""
MigPAL PDF Generator Module
Genera reportes PDF profesionales para casos migratorios
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

# PDF output directory
PDF_DIR = Path(__file__).parent.parent.parent / "data" / "reports"
PDF_DIR.mkdir(parents=True, exist_ok=True)


class MigPALReport(FPDF):
    """Custom PDF class for MigPAL reports"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Logo placeholder
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(0, 102, 204)  # Blue
        self.cell(0, 10, "MigPAL", 0, 0, "L")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Global Migration Assistant", 0, 1, "R")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0,
            10,
            f'Page {self.page_no()}/{{nb}} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | MigPAL - t.me/MigPAL_Bot',
            0,
            0,
            "C",
        )

    def chapter_title(self, title: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, title, 0, 1, "L")
        self.set_draw_color(0, 102, 204)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(5)

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(51, 51, 51)
        self.cell(0, 8, title, 0, 1, "L")

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def key_value(self, key: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(51, 51, 51)
        self.cell(60, 6, f"{key}:", 0, 0, "L")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, str(value) if value else "N/A", 0, 1, "L")

    def add_table(self, headers: list, data: list):
        """Add a simple table"""
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 102, 204)
        self.set_text_color(255, 255, 255)

        col_width = 190 / len(headers)
        for header in headers:
            self.cell(col_width, 8, header, 1, 0, "C", True)
        self.ln()

        self.set_font("Helvetica", "", 9)
        self.set_text_color(51, 51, 51)
        fill = False
        for row in data:
            if fill:
                self.set_fill_color(240, 240, 240)
            else:
                self.set_fill_color(255, 255, 255)
            for item in row:
                self.cell(col_width, 7, str(item)[:30], 1, 0, "L", fill)
            self.ln()
            fill = not fill


def generate_case_report_pdf(user_data: dict[str, Any], user_id: int) -> str | None:
    """
    Generate a professional PDF report for a migration case
    Returns the file path of the generated PDF
    """
    try:
        pdf = MigPALReport()
        pdf.alias_nb_pages()
        pdf.add_page()

        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})
        education = profile.get("education", {})
        work = profile.get("work", {})
        languages = profile.get("languages", {})
        history = profile.get("history", {})
        financial = profile.get("financial", {})
        route = user_data.get("selected_route", {})
        family = user_data.get("family_members", [])
        preferences = user_data.get("preferences", {})

        # Title
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 15, "Migration Case Report", 0, 1, "C")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 8, f'Case ID: MIG-{user_id}-{datetime.now().strftime("%Y%m%d")}', 0, 1, "C")
        pdf.ln(10)

        # Personal Information
        pdf.chapter_title("1. Personal Information")
        pdf.key_value("Full Name", personal.get("name"))
        pdf.key_value("Date of Birth", personal.get("birth_date"))
        pdf.key_value("Nationality", personal.get("nationality"))
        pdf.key_value("Current Country", personal.get("current_country"))
        pdf.key_value("Current City", personal.get("current_city"))
        pdf.key_value("Email", personal.get("email"))
        pdf.key_value("Phone", personal.get("phone"))
        pdf.ln(5)

        # Education
        pdf.chapter_title("2. Education")
        pdf.key_value("Highest Level", education.get("level"))
        pdf.key_value("Status", education.get("status"))
        pdf.key_value("Field of Study", education.get("field"))
        pdf.key_value("Degree/Career", education.get("career"))
        pdf.ln(5)

        # Work Experience
        pdf.chapter_title("3. Work Experience")
        pdf.key_value("Current Status", work.get("status"))
        pdf.key_value("Profession", work.get("profession"))
        pdf.key_value("Years of Experience", work.get("experience"))
        pdf.key_value("LinkedIn/CV", work.get("linkedin", "Not provided"))
        pdf.ln(5)

        # Languages
        pdf.chapter_title("4. Language Skills")
        pdf.key_value("English Level", languages.get("english"))
        pdf.ln(5)

        # Immigration History
        pdf.chapter_title("5. Immigration History")
        pdf.key_value("Previous Visas", history.get("visas", "None"))
        pdf.key_value("Visa Rejections", history.get("rejections", "No"))
        pdf.key_value("Criminal Record", history.get("criminal", "No"))
        pdf.key_value("Health Conditions", history.get("health", "No"))
        pdf.ln(5)

        # Financial Information
        pdf.chapter_title("6. Financial Information")
        pdf.key_value("Available Savings", financial.get("savings"))
        pdf.key_value("Budget for Process", preferences.get("budget"))
        pdf.ln(5)

        # Migration Route
        pdf.add_page()
        pdf.chapter_title("7. Selected Migration Route")
        pdf.key_value("Destination Country", route.get("country"))
        pdf.key_value("Visa Type", route.get("visa_type"))
        pdf.key_value("Target State/Region", route.get("state"))
        pdf.key_value("Target City", route.get("city"))
        pdf.key_value("Housing Preference", route.get("housing"))
        pdf.ln(5)

        # Migration Preferences
        pdf.chapter_title("8. Migration Preferences")
        pdf.key_value("Primary Reason", preferences.get("reason"))
        pdf.key_value("Timeline", preferences.get("timeline"))
        pdf.key_value("Climate Preference", preferences.get("climate"))
        pdf.key_value("City Size Preference", preferences.get("city_size"))
        pdf.ln(5)

        # Family Members
        if family:
            pdf.chapter_title("9. Family Members")
            headers = ["Relation", "Name", "Birth Date", "Education", "English"]
            data = []
            for member in family:
                data.append(
                    [
                        member.get("relation", "N/A"),
                        member.get("name", "N/A"),
                        member.get("birth_date", "N/A"),
                        member.get("education", "N/A"),
                        member.get("english", "N/A"),
                    ]
                )
            pdf.add_table(headers, data)
            pdf.ln(5)

        # Documents
        documents = user_data.get("documents", [])
        if documents:
            pdf.chapter_title("10. Uploaded Documents")
            for i, doc in enumerate(documents, 1):
                pdf.body_text(
                    f"{i}. {doc.get('file_name', doc.get('type', 'Document'))} - Uploaded: {doc.get('uploaded_at', 'N/A')}"
                )

        # Next Steps
        pdf.add_page()
        pdf.chapter_title("11. Recommended Next Steps")

        steps = [
            "1. Complete all required documentation for your selected visa type",
            "2. Verify document validity dates and renew if necessary",
            "3. Prepare financial proof according to destination country requirements",
            "4. Schedule required medical examinations",
            "5. Take language proficiency tests if required (IELTS, TOEFL, etc.)",
            "6. Research and connect with immigration lawyers if needed",
            "7. Join migrant communities for support and advice",
            "8. Create a detailed timeline for your migration process",
            "9. Prepare for cultural adaptation in your destination country",
            "10. Set up emergency contacts and support network",
        ]

        for step in steps:
            pdf.body_text(step)

        pdf.ln(10)

        # Disclaimer
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(128, 128, 128)
        pdf.multi_cell(
            0,
            5,
            "DISCLAIMER: This report is generated by MigPAL for informational purposes only. "
            "It does not constitute legal advice. Immigration laws and requirements change frequently. "
            "Always verify information with official government sources and consult with qualified "
            "immigration professionals before making decisions. MigPAL is not responsible for any "
            "actions taken based on this report.",
        )

        # Save PDF
        filename = f"MigPAL_Report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = PDF_DIR / filename
        pdf.output(str(filepath))

        return str(filepath)

    except Exception as e:
        import logging

        logging.error(f"Error generating PDF: {e}")
        return None


def generate_checklist_pdf(user_data: dict[str, Any], checklist: list, user_id: int) -> str | None:
    """Generate a document checklist PDF"""
    try:
        pdf = MigPALReport()
        pdf.alias_nb_pages()
        pdf.add_page()

        route = user_data.get("selected_route", {})
        personal = user_data.get("profile", {}).get("personal", {})

        # Title
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 15, "Document Checklist", 0, 1, "C")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f'{route.get("country", "N/A")} - {route.get("visa_type", "N/A")}', 0, 1, "C")
        pdf.ln(10)

        # Applicant Info
        pdf.chapter_title("Applicant Information")
        pdf.key_value("Name", personal.get("name"))
        pdf.key_value("Nationality", personal.get("nationality"))
        pdf.ln(5)

        # Required Documents
        pdf.chapter_title("Required Documents")
        for doc in checklist:
            if doc.get("required"):
                status = "[ ]"  # Checkbox
                validity = f" (Valid: {doc['validity']})" if doc.get("validity") else ""
                pdf.body_text(f"{status} {doc['name']}{validity}")
                if doc.get("notes"):
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.set_text_color(128, 128, 128)
                    pdf.cell(10)  # Indent
                    pdf.multi_cell(0, 5, f"Note: {doc['notes']}")
                    pdf.set_text_color(51, 51, 51)

        pdf.ln(5)

        # Optional Documents
        optional = [d for d in checklist if not d.get("required")]
        if optional:
            pdf.chapter_title("Optional Documents")
            for doc in optional:
                pdf.body_text(f"[ ] {doc['name']}")

        # Save PDF
        filename = f"MigPAL_Checklist_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = PDF_DIR / filename
        pdf.output(str(filepath))

        return str(filepath)

    except Exception as e:
        import logging

        logging.error(f"Error generating checklist PDF: {e}")
        return None
