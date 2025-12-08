"""
Export service for generating reports in various formats
"""

import csv
import io
import json
from datetime import datetime
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ExportService:
    """Service for exporting data in various formats"""

    @staticmethod
    def export_to_csv(data: List[dict], columns: List[str] = None) -> str:
        """
        Export data to CSV format.

        Args:
            data: List of dictionaries containing data
            columns: Optional list of column names (uses all keys if None)

        Returns:
            CSV string
        """
        if not data:
            return ""

        # Determine columns
        if not columns:
            columns = list(data[0].keys()) if data else []

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")

        writer.writeheader()
        for row in data:
            # Filter out None values and convert to string
            filtered_row = {
                k: str(v) if v is not None else "" for k, v in row.items() if k in columns
            }
            writer.writerow(filtered_row)

        return output.getvalue()

    @staticmethod
    def export_to_json(data: List[dict]) -> str:
        """
        Export data to JSON format.

        Args:
            data: List of dictionaries containing data

        Returns:
            JSON string
        """
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def export_patients_to_pdf(patients: List[dict], title: str = "Patient Report") -> bytes:
        """
        Export patient data to PDF format.

        Args:
            patients: List of patient dictionaries
            title: Report title

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)

        # Container for the 'Flowable' objects
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=30,
            alignment=1,  # Center
        )

        # Title
        elements.append(Paragraph(title, title_style))
        elements.append(
            Paragraph(
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        if not patients:
            elements.append(Paragraph("No patients found.", styles["Normal"]))
        else:
            # Prepare table data
            table_data = [
                [
                    "ID",
                    "Name",
                    "Date of Birth",
                    "Gender",
                    "Email",
                    "Phone",
                ]
            ]

            for patient in patients:
                table_data.append(
                    [
                        str(patient.get("id", "")),
                        f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                        str(patient.get("date_of_birth", "")),
                        str(patient.get("gender", "")),
                        str(patient.get("email", "")),
                        str(patient.get("phone", "")),
                    ]
                )

            # Create table
            table = Table(
                table_data,
                colWidths=[
                    0.5 * inch,
                    1.5 * inch,
                    1 * inch,
                    0.7 * inch,
                    1.5 * inch,
                    1 * inch,
                ],
            )

            # Add style to table
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )

            elements.append(table)
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(
                Paragraph(
                    f"Total Patients: {len(patients)}",
                    styles["Normal"],
                )
            )

        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
