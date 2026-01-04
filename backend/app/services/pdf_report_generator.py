"""
MigPAL PDF Report Generator - Generador de Reportes PDF
Genera reportes profesionales en PDF para clientes

TIPOS DE REPORTES:
1. Diagnóstico Inicial - Evaluación de viabilidad
2. Perfil del Cliente - Resumen de información
3. Plan de Migración - Ciudad, vivienda, trabajo, visa
4. Comparación de Ciudades - Análisis lado a lado
5. Checklist de Documentos - Lista de requisitos
"""

import io
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Intentar importar reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, ListFlowable, ListItem, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available - PDF generation will be disabled")


class PDFReportGenerator:
    """Generador de reportes PDF"""
    
    def __init__(self):
        self.page_size = letter
        self.margin = 0.75 * inch
        
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()
        
        # Colores corporativos
        self.colors = {
            "primary": colors.HexColor("#2196F3"),
            "secondary": colors.HexColor("#4CAF50"),
            "accent": colors.HexColor("#FF9800"),
            "dark": colors.HexColor("#37474F"),
            "light": colors.HexColor("#ECEFF1"),
            "success": colors.HexColor("#4CAF50"),
            "warning": colors.HexColor("#FFC107"),
            "danger": colors.HexColor("#F44336"),
        }
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados"""
        if not REPORTLAB_AVAILABLE:
            return
        
        # Título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.colors["primary"],
            spaceAfter=20,
            alignment=TA_CENTER,
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.colors["dark"],
            spaceAfter=12,
            spaceBefore=20,
        ))
        
        # Sección
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=self.colors["primary"],
            spaceAfter=10,
            spaceBefore=15,
            borderColor=self.colors["primary"],
            borderWidth=1,
            borderPadding=5,
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.colors["dark"],
            spaceAfter=8,
            alignment=TA_JUSTIFY,
        ))
        
        # Texto destacado
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.colors["secondary"],
            spaceAfter=8,
            fontName='Helvetica-Bold',
        ))
        
        # Pie de página
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
        ))
    
    def _create_header(self, title: str, subtitle: str = "") -> List:
        """Crea el encabezado del reporte"""
        elements = []
        
        # Logo/Título
        elements.append(Paragraph("🌍 MigPAL", self.styles['MainTitle']))
        elements.append(Paragraph("Tu Consultor de Migración", self.styles['BodyText']))
        elements.append(Spacer(1, 20))
        
        # Título del reporte
        elements.append(Paragraph(title, self.styles['SubTitle']))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['BodyText']))
        
        # Línea separadora
        elements.append(HRFlowable(width="100%", thickness=2, color=self.colors["primary"]))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_footer(self) -> str:
        """Crea el pie de página"""
        return f"MigPAL - Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | www.migpal.ai"
    
    def _create_info_table(self, data: List[List[str]], col_widths: List[float] = None) -> Table:
        """Crea una tabla de información"""
        if col_widths is None:
            col_widths = [2*inch, 4*inch]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.colors["light"]),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors["dark"]),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        return table
    
    def _create_score_table(self, scores: Dict[str, float]) -> Table:
        """Crea una tabla de scores"""
        # Traducir categorías
        category_labels = {
            "costo_vida": "💰 Costo de Vida",
            "seguridad": "🛡️ Seguridad",
            "oportunidades": "💼 Oportunidades",
            "educacion": "🎓 Educación",
            "salud": "🏥 Salud",
            "transporte": "🚇 Transporte",
            "comunidad_latina": "🤝 Comunidad Latina",
            "clima": "☀️ Clima",
            "calidad_vida": "🌟 Calidad de Vida",
        }
        
        data = [["Categoría", "Score", "Nivel"]]
        for key, score in scores.items():
            label = category_labels.get(key, key)
            level = "Excelente" if score >= 80 else "Bueno" if score >= 60 else "Regular" if score >= 40 else "Bajo"
            data.append([label, f"{score:.0f}/100", level])
        
        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors["primary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors["light"]]),
        ]))
        return table
    
    def generate_diagnostic_report(
        self,
        client_name: str,
        client_data: Dict[str, Any],
        visa_analysis: Dict[str, Any],
        recommendations: List[str]
    ) -> Optional[bytes]:
        """Genera reporte de diagnóstico"""
        if not REPORTLAB_AVAILABLE:
            return None
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        elements = []
        
        # Header
        elements.extend(self._create_header(
            "REPORTE DE DIAGNÓSTICO",
            f"Cliente: {client_name}"
        ))
        
        # Fecha
        elements.append(Paragraph(
            f"Fecha: {datetime.now().strftime('%d de %B de %Y')}",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 20))
        
        # Información del cliente
        elements.append(Paragraph("📋 INFORMACIÓN DEL CLIENTE", self.styles['SectionTitle']))
        
        personal = client_data.get("profile", {}).get("personal", {})
        info_data = [
            ["Nombre:", personal.get("name", "N/A")],
            ["Nacionalidad:", personal.get("nationality", "N/A")],
            ["País actual:", personal.get("current_country", "N/A")],
            ["Ciudad actual:", personal.get("current_city", "N/A")],
        ]
        elements.append(self._create_info_table(info_data))
        elements.append(Spacer(1, 20))
        
        # Análisis de visa
        elements.append(Paragraph("🛂 ANÁLISIS DE VISA", self.styles['SectionTitle']))
        
        visa_type = visa_analysis.get("recommended_visa", "Por determinar")
        probability = visa_analysis.get("probability", 0)
        
        visa_data = [
            ["Visa recomendada:", visa_type],
            ["Probabilidad de éxito:", f"{probability}%"],
            ["Tiempo estimado:", visa_analysis.get("timeline", "6-12 meses")],
        ]
        elements.append(self._create_info_table(visa_data))
        elements.append(Spacer(1, 20))
        
        # Recomendaciones
        elements.append(Paragraph("💡 RECOMENDACIONES", self.styles['SectionTitle']))
        
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"{i}. {rec}", self.styles['BodyText']))
        
        elements.append(Spacer(1, 30))
        
        # Próximos pasos
        elements.append(Paragraph("📌 PRÓXIMOS PASOS", self.styles['SectionTitle']))
        next_steps = [
            "Completar el perfilamiento detallado ($50 USD)",
            "Reunir documentos base según checklist",
            "Agendar sesión de consultoría personalizada",
        ]
        for step in next_steps:
            elements.append(Paragraph(f"• {step}", self.styles['BodyText']))
        
        # Footer
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Paragraph(self._create_footer(), self.styles['Footer']))
        
        # Generar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_city_report(
        self,
        city_data: Dict[str, Any],
        include_housing: bool = True,
        include_jobs: bool = True
    ) -> Optional[bytes]:
        """Genera reporte de ciudad"""
        if not REPORTLAB_AVAILABLE:
            return None
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        elements = []
        
        city_name = city_data.get("name", "Ciudad")
        state = city_data.get("state_code", "")
        
        # Header
        elements.extend(self._create_header(
            f"REPORTE DE CIUDAD",
            f"{city_name}, {state}"
        ))
        
        # Resumen
        elements.append(Paragraph("📊 RESUMEN EJECUTIVO", self.styles['SectionTitle']))
        
        description = city_data.get("description", "")
        if description:
            elements.append(Paragraph(description, self.styles['BodyText']))
        elements.append(Spacer(1, 15))
        
        # Datos generales
        elements.append(Paragraph("📋 DATOS GENERALES", self.styles['SectionTitle']))
        
        general_data = [
            ["Población:", f"{city_data.get('population', 0):,}"],
            ["Área metropolitana:", f"{city_data.get('metro_population', 0):,}"],
            ["Ingreso medio:", f"${city_data.get('median_income', 0):,}/año"],
            ["Comunidad latina:", f"{city_data.get('latino_pct', 0):.1f}%"],
            ["Clima:", city_data.get("climate", "N/A")],
        ]
        elements.append(self._create_info_table(general_data))
        elements.append(Spacer(1, 20))
        
        # Scores
        elements.append(Paragraph("📈 SCORES POR CATEGORÍA", self.styles['SectionTitle']))
        scores = city_data.get("scores", {})
        if scores:
            elements.append(self._create_score_table(scores))
        elements.append(Spacer(1, 20))
        
        # Vivienda
        if include_housing:
            elements.append(Paragraph("🏠 VIVIENDA", self.styles['SectionTitle']))
            
            housing_data = [
                ["Precio mediano casa:", f"${city_data.get('median_home_price', 0):,}"],
                ["Renta 1 habitación:", f"${city_data.get('median_rent_1br', 0):,}/mes"],
                ["Renta 2 habitaciones:", f"${city_data.get('median_rent_2br', 0):,}/mes"],
                ["Renta 3 habitaciones:", f"${city_data.get('median_rent_3br', 0):,}/mes"],
                ["Costo de vida:", f"{city_data.get('cost_of_living_index', 100)} (100=promedio)"],
            ]
            elements.append(self._create_info_table(housing_data))
            elements.append(Spacer(1, 20))
        
        # Empleo
        if include_jobs:
            elements.append(Paragraph("💼 EMPLEO", self.styles['SectionTitle']))
            
            industries = city_data.get("top_industries", [])
            employers = city_data.get("major_employers", [])
            
            job_data = [
                ["Tasa de desempleo:", f"{city_data.get('unemployment_rate', 0):.1f}%"],
                ["Industrias principales:", ", ".join(industries[:3]) if industries else "N/A"],
                ["Empleadores principales:", ", ".join(employers[:3]) if employers else "N/A"],
            ]
            elements.append(self._create_info_table(job_data))
            elements.append(Spacer(1, 20))
        
        # Pros y Contras
        elements.append(Paragraph("✅ VENTAJAS", self.styles['SectionTitle']))
        pros = city_data.get("pros", [])
        for pro in pros:
            elements.append(Paragraph(f"• {pro}", self.styles['BodyText']))
        
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("⚠️ DESVENTAJAS", self.styles['SectionTitle']))
        cons = city_data.get("cons", [])
        for con in cons:
            elements.append(Paragraph(f"• {con}", self.styles['BodyText']))
        
        # Footer
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Paragraph(self._create_footer(), self.styles['Footer']))
        
        # Generar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_comparison_report(
        self,
        city1_data: Dict[str, Any],
        city2_data: Dict[str, Any]
    ) -> Optional[bytes]:
        """Genera reporte de comparación de ciudades"""
        if not REPORTLAB_AVAILABLE:
            return None
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        elements = []
        
        city1_name = city1_data.get("name", "Ciudad 1")
        city2_name = city2_data.get("name", "Ciudad 2")
        
        # Header
        elements.extend(self._create_header(
            "COMPARACIÓN DE CIUDADES",
            f"{city1_name} vs {city2_name}"
        ))
        
        # Tabla comparativa
        elements.append(Paragraph("📊 COMPARACIÓN GENERAL", self.styles['SectionTitle']))
        
        comparison_data = [
            ["Métrica", city1_name, city2_name],
            ["Población", f"{city1_data.get('population', 0):,}", f"{city2_data.get('population', 0):,}"],
            ["Ingreso medio", f"${city1_data.get('median_income', 0):,}", f"${city2_data.get('median_income', 0):,}"],
            ["Renta 2BR", f"${city1_data.get('median_rent_2br', 0):,}", f"${city2_data.get('median_rent_2br', 0):,}"],
            ["Comunidad latina", f"{city1_data.get('latino_pct', 0):.1f}%", f"{city2_data.get('latino_pct', 0):.1f}%"],
            ["Seguridad", f"{100 - city1_data.get('crime_index', 50)}/100", f"{100 - city2_data.get('crime_index', 50)}/100"],
        ]
        
        table = Table(comparison_data, colWidths=[2*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors["primary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors["light"]]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        # Scores comparativos
        elements.append(Paragraph("📈 COMPARACIÓN DE SCORES", self.styles['SectionTitle']))
        
        scores1 = city1_data.get("scores", {})
        scores2 = city2_data.get("scores", {})
        
        category_labels = {
            "costo_vida": "Costo de Vida",
            "seguridad": "Seguridad",
            "oportunidades": "Oportunidades",
            "educacion": "Educación",
            "salud": "Salud",
            "transporte": "Transporte",
            "comunidad_latina": "Com. Latina",
            "clima": "Clima",
            "calidad_vida": "Calidad Vida",
        }
        
        score_data = [["Categoría", city1_name, city2_name, "Ganador"]]
        for key in scores1.keys():
            s1 = scores1.get(key, 50)
            s2 = scores2.get(key, 50)
            winner = city1_name if s1 > s2 else city2_name if s2 > s1 else "Empate"
            label = category_labels.get(key, key)
            score_data.append([label, f"{s1:.0f}", f"{s2:.0f}", winner])
        
        score_table = Table(score_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors["secondary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(score_table)
        
        # Footer
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Paragraph(self._create_footer(), self.styles['Footer']))
        
        # Generar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_migration_plan_report(
        self,
        client_name: str,
        client_data: Dict[str, Any],
        selected_city: Dict[str, Any],
        visa_info: Dict[str, Any],
        timeline: List[Dict[str, str]]
    ) -> Optional[bytes]:
        """Genera reporte de plan de migración completo"""
        if not REPORTLAB_AVAILABLE:
            return None
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        elements = []
        
        # Header
        elements.extend(self._create_header(
            "PLAN DE MIGRACIÓN",
            f"Preparado para: {client_name}"
        ))
        
        # Resumen ejecutivo
        elements.append(Paragraph("📋 RESUMEN EJECUTIVO", self.styles['SectionTitle']))
        
        city_name = selected_city.get("name", "N/A")
        state = selected_city.get("state_code", "")
        visa_type = visa_info.get("type", "Por determinar")
        
        summary = f"""
        Este plan de migración ha sido diseñado específicamente para {client_name}, 
        con destino a {city_name}, {state}. El tipo de visa recomendado es {visa_type}.
        A continuación se detallan todos los aspectos del plan.
        """
        elements.append(Paragraph(summary, self.styles['BodyText']))
        elements.append(Spacer(1, 20))
        
        # Ciudad destino
        elements.append(Paragraph("🏙️ CIUDAD DESTINO", self.styles['SectionTitle']))
        
        city_info = [
            ["Ciudad:", f"{city_name}, {state}"],
            ["Población:", f"{selected_city.get('population', 0):,}"],
            ["Ingreso medio:", f"${selected_city.get('median_income', 0):,}/año"],
            ["Costo de vida:", f"{selected_city.get('cost_of_living_index', 100)} (100=promedio)"],
            ["Comunidad latina:", f"{selected_city.get('latino_pct', 0):.1f}%"],
        ]
        elements.append(self._create_info_table(city_info))
        elements.append(Spacer(1, 20))
        
        # Visa
        elements.append(Paragraph("🛂 ESTRATEGIA DE VISA", self.styles['SectionTitle']))
        
        visa_data = [
            ["Tipo de visa:", visa_type],
            ["Probabilidad:", f"{visa_info.get('probability', 0)}%"],
            ["Tiempo de proceso:", visa_info.get("processing_time", "6-12 meses")],
            ["Costo estimado:", f"${visa_info.get('cost', 0):,}"],
        ]
        elements.append(self._create_info_table(visa_data))
        elements.append(Spacer(1, 20))
        
        # Timeline
        elements.append(Paragraph("📅 CRONOGRAMA", self.styles['SectionTitle']))
        
        timeline_data = [["Fase", "Descripción", "Duración"]]
        for item in timeline:
            timeline_data.append([
                item.get("phase", ""),
                item.get("description", ""),
                item.get("duration", "")
            ])
        
        timeline_table = Table(timeline_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors["accent"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(timeline_table)
        
        # Footer
        elements.append(Spacer(1, 40))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Paragraph(self._create_footer(), self.styles['Footer']))
        
        # Generar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Instancia global
pdf_generator = PDFReportGenerator()


# Funciones helper
def generate_diagnostic_pdf(client_name: str, client_data: Dict, visa_analysis: Dict, recommendations: List[str]) -> Optional[bytes]:
    return pdf_generator.generate_diagnostic_report(client_name, client_data, visa_analysis, recommendations)

def generate_city_pdf(city_data: Dict) -> Optional[bytes]:
    return pdf_generator.generate_city_report(city_data)

def generate_comparison_pdf(city1_data: Dict, city2_data: Dict) -> Optional[bytes]:
    return pdf_generator.generate_comparison_report(city1_data, city2_data)

def generate_migration_plan_pdf(client_name: str, client_data: Dict, city: Dict, visa: Dict, timeline: List[Dict]) -> Optional[bytes]:
    return pdf_generator.generate_migration_plan_report(client_name, client_data, city, visa, timeline)
