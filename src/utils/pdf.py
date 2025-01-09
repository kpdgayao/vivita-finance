from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

class FormPrinter:
    def generate_prof_pdf(self, prof_data: dict) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        
        elements = []
        
        # Add header
        elements.append(Paragraph("VIVITA PHILIPPINES", title_style))
        elements.append(Paragraph("PURCHASE REQUEST AND ORDER FORM", title_style))
        
        # Add form details
        header_data = [
            ["PROF No:", prof_data['form_number'], "Date:", prof_data['date']],
            ["Requestor:", prof_data['requestor'], "Department:", prof_data['department']],
            ["Supplier:", prof_data['supplier'], "", ""]
        ]
        
        header_table = Table(header_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Add items table
        items_data = [["Description", "Quantity", "Unit", "Unit Price", "Amount"]]
        for item in prof_data['items']:
            amount = float(item['quantity']) * float(item['unit_price'])
            items_data.append([
                item['item_description'],
                item['quantity'],
                item['unit'],
                f"₱{item['unit_price']:,.2f}",
                f"₱{amount:,.2f}"
            ])
        
        # Add total row
        items_data.append(["", "", "", "Total:", f"₱{prof_data['total_amount']:,.2f}"])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1.25*inch, 1.25*inch])
        items_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -2), 0.25, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(items_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
