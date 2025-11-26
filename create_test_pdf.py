"""
Generate realistic immigration test PDFs for OLI testing
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, timedelta
import os

def create_bank_statement_pdf(filename="test_documents/releve_bancaire.pdf"):
    """Create a realistic certified bank statement PDF"""
    
    os.makedirs("test_documents", exist_ok=True)
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1a365d')
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666')
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#2c5282')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    elements = []
    
    # Bank Header
    elements.append(Paragraph("BANQUE NATIONALE DE PARIS", title_style))
    elements.append(Paragraph("Certified Bank Statement / Relevé Bancaire Certifié", header_style))
    elements.append(Paragraph("Document officiel pour Immigration Canada", header_style))
    elements.append(Spacer(1, 20))
    
    # Statement Date (OLD - will trigger warning)
    statement_date = datetime(2024, 1, 15)  # Old date!
    
    # Account Holder Info
    elements.append(Paragraph("INFORMATIONS DU TITULAIRE / ACCOUNT HOLDER", section_style))
    
    holder_data = [
        ["Nom / Name:", "Sophie Marie Martin"],
        ["Date de naissance / DOB:", "April 12, 1985"],
        ["Adresse / Address:", "123 Rue de la Paix, Paris 75001, France"],
        ["Numéro de compte / Account #:", "FR76 1234 5678 9012 3456 7890 123"],
        ["Type de compte / Account Type:", "Compte Courant / Checking Account"],
        ["UCI (Immigration):", "UCI-99887766"],
        ["Courriel / Email:", "sophie.martin@email.fr"],
        ["Téléphone / Phone:", "+33 6 12 34 56 78"],
    ]
    
    holder_table = Table(holder_data, colWidths=[2.5*inch, 4.5*inch])
    holder_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(holder_table)
    elements.append(Spacer(1, 15))
    
    # Financial Summary
    elements.append(Paragraph("SOMMAIRE FINANCIER / FINANCIAL SUMMARY", section_style))
    elements.append(Paragraph(f"Période: {(statement_date - timedelta(days=180)).strftime('%Y-%m-%d')} au {statement_date.strftime('%Y-%m-%d')}", normal_style))
    
    # LOW balance - will trigger LICO warning!
    financial_data = [
        ["Description", "Montant / Amount (CAD)"],
        ["Solde d'ouverture / Opening Balance", "4,250.00 $"],
        ["Total des dépôts / Total Deposits", "12,500.00 $"],
        ["Total des retraits / Total Withdrawals", "11,750.00 $"],
        ["Solde de clôture / Closing Balance", "5,000.00 $"],
        ["Solde moyen (6 mois) / Average Balance", "5,000.00 $"],
    ]
    
    fin_table = Table(financial_data, colWidths=[4.5*inch, 2.5*inch])
    fin_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff5f5')),  # Highlight low balance
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 15))
    
    # Transaction History
    elements.append(Paragraph("HISTORIQUE DES TRANSACTIONS / TRANSACTION HISTORY", section_style))
    
    transactions = [
        ["Date", "Description", "Débit", "Crédit", "Solde"],
        ["2024-01-15", "Virement entrant / Transfer In", "", "2,500.00 $", "5,000.00 $"],
        ["2024-01-10", "Loyer / Rent Payment", "1,200.00 $", "", "2,500.00 $"],
        ["2024-01-05", "Salaire / Salary", "", "3,500.00 $", "3,700.00 $"],
        ["2023-12-28", "Achats / Shopping", "450.00 $", "", "200.00 $"],
        ["2023-12-20", "Virement entrant / Transfer In", "", "650.00 $", "650.00 $"],
        ["2023-12-15", "Factures / Bills", "800.00 $", "", "0.00 $"],
        ["2023-12-01", "Salaire / Salary", "", "3,500.00 $", "800.00 $"],
    ]
    
    trans_table = Table(transactions, colWidths=[1*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
    trans_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    elements.append(trans_table)
    elements.append(Spacer(1, 20))
    
    # LICO Reference Box
    elements.append(Paragraph("RÉFÉRENCE LICO / LICO REFERENCE", section_style))
    
    lico_note = """
    <b>Note importante:</b> Selon les exigences d'Immigration, Réfugiés et Citoyenneté Canada (IRCC), 
    le seuil LICO (Low Income Cut-Off) pour une personne seule est de <b>20,635 $ CAD</b> 
    (ou 28,185 $ CAD selon les dernières mises à jour 2024).
    <br/><br/>
    <font color="red"><b>Le solde actuel de 5,000 $ CAD est inférieur au seuil requis.</b></font>
    """
    elements.append(Paragraph(lico_note, normal_style))
    elements.append(Spacer(1, 20))
    
    # Certification
    elements.append(Paragraph("CERTIFICATION BANCAIRE / BANK CERTIFICATION", section_style))
    
    cert_text = f"""
    Je soussigné(e), Jean-Pierre Dubois, Directeur de Succursale, certifie que ce relevé 
    est un document officiel de la Banque Nationale de Paris et que les informations 
    contenues sont exactes à la date du <b>{statement_date.strftime('%d %B %Y')}</b>.
    <br/><br/>
    Ce document est délivré pour les besoins d'une demande d'immigration au Canada.
    """
    elements.append(Paragraph(cert_text, normal_style))
    elements.append(Spacer(1, 30))
    
    # Signature area
    sig_data = [
        ["_" * 40, "_" * 40],
        ["Jean-Pierre Dubois", f"Date: {statement_date.strftime('%Y-%m-%d')}"],
        ["Directeur de Succursale", "Tampon officiel"],
    ]
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(sig_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer = """
    <font size="8" color="#666666">
    Document ID: BNP-2024-001-CERT | Ce document est protégé et ne peut être falsifié.
    <br/>
    Banque Nationale de Paris - SWIFT: BNPAFRPP | Service Immigration: immigration@bnp.fr
    </font>
    """
    elements.append(Paragraph(footer, ParagraphStyle('Footer', alignment=TA_CENTER)))
    
    doc.build(elements)
    print(f"[OK] Created: {filename}")
    return filename


def create_immigration_form_pdf(filename="test_documents/formulaire_immigration.pdf"):
    """Create a realistic immigration application form PDF"""
    
    os.makedirs("test_documents", exist_ok=True)
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#c41e3a')  # Canada red
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#333333')
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=11,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#1a365d'),
        borderPadding=5,
    )
    
    elements = []
    
    # Header with Canada branding
    elements.append(Paragraph("IMMIGRATION, REFUGEES AND CITIZENSHIP CANADA", title_style))
    elements.append(Paragraph("IMMIGRATION, RÉFUGIÉS ET CITOYENNETÉ CANADA", title_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Application for Permanent Residence - Economic Class", subtitle_style))
    elements.append(Paragraph("Demande de résidence permanente - Catégorie économique", subtitle_style))
    elements.append(Paragraph("IMM 0008 (06-2024)", ParagraphStyle('FormID', alignment=TA_CENTER, fontSize=9)))
    elements.append(Spacer(1, 15))
    
    # Section 1: Personal Information
    elements.append(Paragraph("SECTION A: PERSONAL DETAILS / RENSEIGNEMENTS PERSONNELS", section_style))
    
    personal_data = [
        ["UCI (Unique Client Identifier):", "UCI-99887766"],
        ["Family Name / Nom de famille:", "Martin"],
        ["Given Names / Prénoms:", "Sophie Marie"],
        ["Date of Birth / Date de naissance:", "1985-04-12"],
        ["Country of Birth / Pays de naissance:", "France"],
        ["Country of Citizenship / Pays de citoyenneté:", "France"],
        ["Current Country of Residence:", "France"],
        ["Passport Number / No de passeport:", "12AB34567"],
        ["Passport Expiry / Expiration:", "2026-08-15"],
        ["Email / Courriel:", "sophie.martin@email.fr"],
        ["Phone / Téléphone:", "+33 6 12 34 56 78"],
        ["Marital Status / État civil:", "Single / Célibataire"],
    ]
    
    personal_table = Table(personal_data, colWidths=[2.8*inch, 4.2*inch])
    personal_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 10))
    
    # Section 2: Contact Information
    elements.append(Paragraph("SECTION B: ADDRESS / ADRESSE", section_style))
    
    address_data = [
        ["Street Address / Adresse:", "123 Rue de la Paix"],
        ["City / Ville:", "Paris"],
        ["Province/State:", "Île-de-France"],
        ["Postal Code / Code postal:", "75001"],
        ["Country / Pays:", "France"],
    ]
    
    address_table = Table(address_data, colWidths=[2.8*inch, 4.2*inch])
    address_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ]))
    elements.append(address_table)
    elements.append(Spacer(1, 10))
    
    # Section 3: Financial Information
    elements.append(Paragraph("SECTION C: PROOF OF FUNDS / PREUVE DE FONDS", section_style))
    
    # Note: Low funds for testing!
    funds_data = [
        ["Total Settlement Funds Available:", "5,000.00 CAD"],
        ["Source of Funds:", "Personal Savings / Bank Account"],
        ["Bank Name:", "Banque Nationale de Paris"],
        ["Account Type:", "Checking Account / Compte courant"],
        ["Statement Date:", "2024-01-15"],  # OLD DATE!
        ["Number of Family Members:", "1 (Principal Applicant only)"],
        ["Required LICO Amount (1 person):", "20,635.00 CAD"],
    ]
    
    funds_table = Table(funds_data, colWidths=[2.8*inch, 4.2*inch])
    funds_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#fff5f5')),  # Highlight low funds
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
    ]))
    elements.append(funds_table)
    
    # Warning box
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#c53030'),
        backColor=colors.HexColor('#fff5f5'),
        borderPadding=10,
    )
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "<b>WARNING / AVERTISSEMENT:</b> The declared settlement funds (5,000 CAD) appear to be "
        "below the required LICO threshold (20,635 CAD) for a single applicant. Please provide "
        "additional proof of funds or a co-signer.",
        warning_style
    ))
    elements.append(Spacer(1, 10))
    
    # Section 4: Declaration
    elements.append(Paragraph("SECTION D: DECLARATION", section_style))
    
    declaration = """
    I declare that the information I have given in this application is truthful, complete and correct.
    I understand that misrepresentation is an offence under section 127 of the Immigration and Refugee 
    Protection Act and may result in a finding of inadmissibility or removal from Canada.
    <br/><br/>
    Je déclare que les renseignements fournis dans cette demande sont véridiques, complets et exacts.
    Je comprends que les fausses déclarations constituent une infraction en vertu de l'article 127 de 
    la Loi sur l'immigration et la protection des réfugiés et peuvent entraîner une décision 
    d'interdiction de territoire ou le renvoi du Canada.
    """
    elements.append(Paragraph(declaration, ParagraphStyle('Declaration', fontSize=9, spaceAfter=15)))
    
    # Signature
    sig_data = [
        ["Signature of Applicant:", "_" * 35, "Date:", "2024-01-20"],
        ["Print Name:", "Sophie Marie Martin", "", ""],
    ]
    sig_table = Table(sig_data, colWidths=[1.5*inch, 2.5*inch, 0.8*inch, 2*inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(sig_table)
    
    # Footer
    elements.append(Spacer(1, 20))
    footer = """
    <font size="8" color="#666666">
    IMM 0008 (06-2024) E | Page 1 of 1 | Protected when completed / Protégé une fois rempli
    <br/>
    Immigration, Refugees and Citizenship Canada | www.canada.ca/immigration
    </font>
    """
    elements.append(Paragraph(footer, ParagraphStyle('Footer', alignment=TA_CENTER)))
    
    doc.build(elements)
    print(f"[OK] Created: {filename}")
    return filename


def create_compliant_statement_pdf(filename="test_documents/releve_conforme.pdf"):
    """Create a COMPLIANT bank statement (good balance, recent date)"""
    
    os.makedirs("test_documents", exist_ok=True)
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, 
                                  alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#1a365d'))
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, 
                                    spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#2c5282'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, spaceAfter=6)
    
    elements = []
    
    # Recent date (compliant)
    statement_date = datetime.now() - timedelta(days=15)
    
    elements.append(Paragraph("ROYAL BANK OF CANADA", title_style))
    elements.append(Paragraph("Certified Bank Statement / Relevé Bancaire Certifié", 
                              ParagraphStyle('Sub', alignment=TA_CENTER, fontSize=10)))
    elements.append(Spacer(1, 20))
    
    # Account Info
    elements.append(Paragraph("ACCOUNT HOLDER INFORMATION", section_style))
    
    holder_data = [
        ["Name:", "Jean-Claude Tremblay"],
        ["Date of Birth:", "1990-07-22"],
        ["Address:", "456 Maple Street, Montreal, QC H2Y 1A1"],
        ["Account Number:", "1234-567-890123"],
        ["UCI:", "UCI-12345678"],
        ["Email:", "jc.tremblay@gmail.com"],
    ]
    
    holder_table = Table(holder_data, colWidths=[2*inch, 5*inch])
    holder_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(holder_table)
    elements.append(Spacer(1, 15))
    
    # Financial Summary - COMPLIANT amounts!
    elements.append(Paragraph("FINANCIAL SUMMARY", section_style))
    elements.append(Paragraph(f"Period: {(statement_date - timedelta(days=180)).strftime('%Y-%m-%d')} to {statement_date.strftime('%Y-%m-%d')}", normal_style))
    
    financial_data = [
        ["Description", "Amount (CAD)"],
        ["Opening Balance", "28,500.00 $"],
        ["Total Deposits", "15,000.00 $"],
        ["Total Withdrawals", "8,500.00 $"],
        ["Closing Balance", "35,000.00 $"],
        ["6-Month Average Balance", "32,500.00 $"],
    ]
    
    fin_table = Table(financial_data, colWidths=[4.5*inch, 2.5*inch])
    fin_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#276749')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0fff4')),  # Green highlight
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 15))
    
    # LICO Compliance Note
    elements.append(Paragraph("LICO COMPLIANCE CHECK", section_style))
    
    compliance_note = f"""
    <font color="#276749"><b>COMPLIANT:</b></font> The average balance of <b>32,500.00 $ CAD</b> 
    exceeds the required LICO threshold of 20,635 $ CAD for a single applicant.
    <br/><br/>
    Statement Date: <b>{statement_date.strftime('%Y-%m-%d')}</b> (within 6 months - VALID)
    """
    elements.append(Paragraph(compliance_note, normal_style))
    elements.append(Spacer(1, 20))
    
    # Certification
    elements.append(Paragraph("CERTIFICATION", section_style))
    cert_text = f"""
    This is to certify that the above information is accurate as of {statement_date.strftime('%B %d, %Y')}.
    This statement is issued for Canadian immigration purposes.
    """
    elements.append(Paragraph(cert_text, normal_style))
    elements.append(Spacer(1, 30))
    
    # Signature
    elements.append(Paragraph("_" * 40, ParagraphStyle('Sig', alignment=TA_LEFT)))
    elements.append(Paragraph("Marie-Claire Gagnon, Branch Manager", normal_style))
    elements.append(Paragraph(f"Date: {statement_date.strftime('%Y-%m-%d')}", normal_style))
    
    doc.build(elements)
    print(f"[OK] Created: {filename}")
    return filename


if __name__ == "__main__":
    print("=" * 50)
    print("OLI Test PDF Generator")
    print("=" * 50)
    print()
    
    # Create test documents
    pdf1 = create_bank_statement_pdf()
    pdf2 = create_immigration_form_pdf()
    pdf3 = create_compliant_statement_pdf()
    
    print()
    print("=" * 50)
    print("Created 3 test PDFs in test_documents/")
    print()
    print("1. releve_bancaire.pdf - Non-compliant (low funds, old date)")
    print("2. formulaire_immigration.pdf - Immigration form with issues")
    print("3. releve_conforme.pdf - Compliant (good funds, recent date)")
    print()
    print("To test: Open these PDFs in Chrome, then use OLI extension")
    print("=" * 50)

