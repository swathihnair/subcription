"""PDF generation service for invoices"""
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from typing import Optional
import html

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from app.models.billing import Invoice
from app.services.invoice_service import InvoiceService


class PDFGenerator:
    """Service for generating PDF documents"""
    
    # Default company info (can be configured via environment variables)
    DEFAULT_COMPANY_INFO = {
        'name': 'SubscriptIQ',
        'address_line1': '123 Business Street',
        'address_line2': 'Suite 100',
        'city': 'San Francisco',
        'state': 'CA',
        'postal_code': '94105',
        'country': 'USA',
        'phone': '+1 (555) 123-4567',
        'email': 'billing@subscriptiq.com',
        'website': 'www.subscriptiq.com'
    }
    
    @staticmethod
    def _sanitize_text(text: str) -> str:
        """
        Sanitize customer-provided text to prevent injection attacks.
        Escape HTML special characters.
        """
        if text is None:
            return ''
        return html.escape(str(text))
    
    @staticmethod
    def _format_currency(amount: Decimal, currency: str = 'USD') -> str:
        """Format currency amount"""
        if currency == 'USD':
            return f'${amount:,.2f}'
        else:
            return f'{amount:,.2f} {currency}'
    
    @staticmethod
    def generate_invoice_pdf(
        invoice_id,
        company_info: Optional[dict] = None
    ) -> BytesIO:
        """
        Generate invoice PDF.
        
        Args:
            invoice_id: Invoice ID (UUID)
            company_info: Optional company information dict
            
        Returns:
            BytesIO buffer containing PDF
            
        Raises:
            ValueError: If invoice not found
        """
        # Fetch invoice with details
        invoice = InvoiceService.get_invoice_with_details(invoice_id)
        
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Use default company info if not provided
        if company_info is None:
            company_info = PDFGenerator.DEFAULT_COMPANY_INFO
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )
        
        # Build PDF content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            spaceBefore=12,
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT
        )
        
        right_align_style = ParagraphStyle(
            'RightAlign',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=TA_RIGHT
        )
        
        # Company header
        story.append(Paragraph(PDFGenerator._sanitize_text(company_info['name']), title_style))
        story.append(Paragraph(PDFGenerator._sanitize_text(company_info['address_line1']), normal_style))
        if company_info.get('address_line2'):
            story.append(Paragraph(PDFGenerator._sanitize_text(company_info['address_line2']), normal_style))
        story.append(Paragraph(
            f"{PDFGenerator._sanitize_text(company_info['city'])}, "
            f"{PDFGenerator._sanitize_text(company_info['state'])} "
            f"{PDFGenerator._sanitize_text(company_info['postal_code'])}",
            normal_style
        ))
        story.append(Paragraph(PDFGenerator._sanitize_text(company_info.get('phone', '')), normal_style))
        story.append(Paragraph(PDFGenerator._sanitize_text(company_info.get('email', '')), normal_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Invoice title and details
        story.append(Paragraph("INVOICE", title_style))
        
        # Invoice info table
        invoice_info_data = [
            ['Invoice Number:', PDFGenerator._sanitize_text(invoice.invoice_number)],
            ['Invoice Date:', invoice.invoice_date.strftime('%B %d, %Y')],
            ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
            ['Status:', PDFGenerator._sanitize_text(invoice.status.upper())]
        ]
        
        if invoice.billing_period_start and invoice.billing_period_end:
            invoice_info_data.append([
                'Billing Period:',
                f"{invoice.billing_period_start.strftime('%B %d, %Y')} - "
                f"{invoice.billing_period_end.strftime('%B %d, %Y')}"
            ])
        
        invoice_info_table = Table(invoice_info_data, colWidths=[1.5 * inch, 3 * inch])
        invoice_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(invoice_info_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Customer billing address
        story.append(Paragraph("Bill To:", heading_style))
        
        customer = invoice.customer
        if customer:
            story.append(Paragraph(PDFGenerator._sanitize_text(customer.company_name or ''), normal_style))
            if customer.billing_address:
                story.append(Paragraph(PDFGenerator._sanitize_text(customer.billing_address), normal_style))
            if customer.billing_city:
                address_line = f"{PDFGenerator._sanitize_text(customer.billing_city)}"
                if customer.billing_state:
                    address_line += f", {PDFGenerator._sanitize_text(customer.billing_state)}"
                if customer.billing_postal_code:
                    address_line += f" {PDFGenerator._sanitize_text(customer.billing_postal_code)}"
                story.append(Paragraph(address_line, normal_style))
            if customer.billing_country:
                story.append(Paragraph(PDFGenerator._sanitize_text(customer.billing_country), normal_style))
            story.append(Paragraph(PDFGenerator._sanitize_text(customer.email), normal_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Line items table
        story.append(Paragraph("Items:", heading_style))
        
        # Build line items table data
        line_items_data = [
            ['Description', 'Qty', 'Unit Price', 'Discount', 'Tax', 'Total']
        ]
        
        currency = invoice.currency or 'USD'
        
        for item in invoice.line_items:
            line_items_data.append([
                PDFGenerator._sanitize_text(item.description),
                str(item.quantity),
                PDFGenerator._format_currency(item.unit_price, currency),
                PDFGenerator._format_currency(item.discount_amount or Decimal('0'), currency),
                PDFGenerator._format_currency(item.tax_amount, currency),
                PDFGenerator._format_currency(item.total_amount, currency)
            ])
        
        # Create line items table
        line_items_table = Table(
            line_items_data,
            colWidths=[2.5 * inch, 0.6 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, 1 * inch]
        )
        
        line_items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Quantity
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Prices
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        story.append(line_items_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Totals section
        totals_data = [
            ['Subtotal:', PDFGenerator._format_currency(invoice.subtotal_amount, currency)],
            ['Tax:', PDFGenerator._format_currency(invoice.tax_amount, currency)],
            ['Total:', PDFGenerator._format_currency(invoice.total_amount, currency)],
        ]
        
        if invoice.amount_paid > 0:
            totals_data.append(['Paid:', PDFGenerator._format_currency(invoice.amount_paid, currency)])
            totals_data.append(['Amount Due:', PDFGenerator._format_currency(invoice.amount_due, currency)])
        
        totals_table = Table(totals_data, colWidths=[4.8 * inch, 2 * inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Payment instructions (if configured and invoice not paid)
        if invoice.status != 'paid' and company_info.get('payment_instructions'):
            story.append(Paragraph("Payment Instructions:", heading_style))
            story.append(Paragraph(
                PDFGenerator._sanitize_text(company_info['payment_instructions']),
                normal_style
            ))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        buffer.seek(0)
        return buffer
