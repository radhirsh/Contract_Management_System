import os
from django.conf import settings
from django.core.files import File
from contracts.models import Contract
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from contractos.services.llm_service import AzureOpenAIService


def _norm_line(text):
    return " ".join((text or "").split()).strip().lower()


def _contract_scenario(contract):
    name = (contract.name or "").lower()
    if 'nda' in name or 'confidential' in name:
        return 'Mutual NDA for exchange of confidential information during business discussions.'
    if 'saas' in name or 'software' in name or 'license' in name:
        return 'Software/SaaS subscription agreement with service levels, payment, security and support terms.'
    if 'support' in name:
        return 'Support services contract with response timelines, uptime commitments and maintenance obligations.'
    if 'consult' in name:
        return 'Consulting services agreement with milestones, deliverables, IP ownership and payment terms.'
    if 'vendor' in name:
        return 'Vendor supply and services agreement with acceptance criteria, invoicing, warranties and termination.'
    return 'Commercial services agreement for enterprise procurement and ongoing service delivery.'


def _generate_contract_text_with_llm(contract):
    """Generate original, realistic contract text using Azure OpenAI when source text is missing."""
    llm = AzureOpenAIService()
    if not llm.is_configured():
        return ""

    scenario = _contract_scenario(contract)
    prompt = f"""Create a realistic contract draft in plain text only (no markdown, no bullet symbols, no JSON).

Context:
- Contract Name: {contract.name}
- Contract ID: {contract.id}
- Vendor: {contract.vendor}
- Status: {contract.status}
- Risk Level: {contract.risk}
- Scenario: {scenario}

Requirements:
1. Write a professional contract with clear headings and numbered clauses.
2. Include these sections: Parties, Definitions, Scope of Services, Term and Termination, Fees and Payment, Confidentiality, Data Protection, Intellectual Property, Warranties, Liability Limitation, Indemnity, Governing Law, Dispute Resolution, Miscellaneous.
3. Keep it realistic and coherent for enterprise use (about 900-1400 words).
4. Do NOT include any redline analysis, recommendations, risk commentary, or "standard/deviation" labels.
5. Output plain text contract content only.
"""

    system_prompt = (
        "You are a senior legal contract drafting assistant. Produce clean and formal contract language "
        "that looks like an original contract document."
    )

    try:
        return (llm.complete(prompt=prompt, system_prompt=system_prompt) or "").strip()
    except Exception:
        return ""


def build_contract_document_text(contract):
    """Build plain-text contract content (no redline/recommendation content)."""
    extracted = (contract.ai_extracted_text or "").strip()
    if extracted:
        lines = extracted.splitlines()
        sanitized = []
        stop_markers = {
            'redline suggestions',
            'generated on',
        }
        blocked_prefixes = (
            'issue:',
            'recommendation:',
            'standard rule / value:',
            'restricted terms / conditions:',
            'deviation rule:',
            'ai recommendation:',
            'reviewer comment:',
        )

        for raw_line in lines:
            line = raw_line.strip()
            low = line.lower()

            if low in stop_markers:
                break

            # Remove old injected redline list items like "1. Issue: ..."
            if '. issue:' in low:
                continue

            if any(low.startswith(prefix) for prefix in blocked_prefixes):
                continue

            sanitized.append(raw_line)

        cleaned = "\n".join(sanitized).strip()
        if cleaned:
            return cleaned

    generated = _generate_contract_text_with_llm(contract)
    if generated:
        return generated

    lines = [
        f"CONTRACT: {contract.name}",
        f"Contract ID: {contract.id}",
        f"Vendor: {contract.vendor}",
        f"Expiry Date: {contract.expiry}",
        f"Version: {contract.version}",
        f"Status: {contract.status}",
        f"Risk Level: {contract.risk}",
        "",
        "Contract content is not available. Upload the original contract file to preserve full text.",
    ]
    return "\n".join(lines)


def generate_contract_pdf(contract, out_path, highlight_lines=None):
    """Generate contract PDF with optional highlighted lines for accepted updates."""
    doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a202c'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph(f"CONTRACT: {contract.name}", title_style))
    story.append(Spacer(1, 6*mm))
    
    # Contract Details Section
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph("Contract Details", heading_style))
    
    # Details table
    details_data = [
        ['Contract ID', str(contract.id)],
        ['Vendor', str(contract.vendor)],
        ['Expiry Date', str(contract.expiry)],
        ['Version', str(contract.version)],
        ['Status', str(contract.status)],
        ['Risk Level', str(contract.risk)],
        ['Created By', str(contract.created_by)],
        ['Uploaded Date', str(contract.uploaded)],
    ]
    
    details_table = Table(details_data, colWidths=[60*mm, 80*mm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a202c')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 10*mm))

    # Contract content section (real content only)
    content_text = build_contract_document_text(contract)
    story.append(Paragraph("Contract Content", heading_style))
    body_style = ParagraphStyle(
        'ContractBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1f2937'),
    )
    body_style_highlight = ParagraphStyle(
        'ContractBodyHighlight',
        parent=body_style,
        textColor=colors.HexColor('#065f46'),  # Even darker green for text
        backColor=colors.HexColor('#bbf7d0'),  # Bright green highlight
        borderPadding=2,
        borderColor=colors.HexColor('#22c55e'),
        borderWidth=1,
        borderRadius=2,
    )
    highlight_norm = {_norm_line(line) for line in (highlight_lines or []) if (line or '').strip()}
    for para in [p.strip() for p in content_text.splitlines() if p.strip()]:
        # Always highlight lines under 'Accepted Amendment Updates' if any highlight lines exist
        if para.startswith('Accepted Amendment Updates') or any(_norm_line(para).endswith(_norm_line(h)) for h in highlight_lines or []):
            use_style = body_style_highlight
        else:
            use_style = body_style_highlight if _norm_line(para) in highlight_norm else body_style
        story.append(Paragraph(para, use_style))
        story.append(Spacer(1, 2*mm))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096'),
        alignment=TA_CENTER
    )
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    
    # Build PDF
    doc.build(story)

def ensure_contract_documents():
    media_root = settings.MEDIA_ROOT
    for contract in Contract.objects.all():
        if not contract.file:
            filename = f"contract_{contract.id}.pdf"
            out_path = os.path.join(media_root, "contracts", filename)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            generate_contract_pdf(contract, out_path)
            with open(out_path, "rb") as f:
                contract.file.save(filename, File(f), save=True)
            print(f"Generated and attached: {filename}")
        else:
            print(f"Already has file: {contract.file.name}")

if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractos.settings')
    django.setup()
    ensure_contract_documents()
