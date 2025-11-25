from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import re
from enum import Enum

app = FastAPI(
    title="OLI Backend API",
    description="Overlay Legal Intelligence - Compliance Analysis Engine",
    version="1.0.0"
)

# CORS for extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RiskLevel(str, Enum):
    CONFORME = "CONFORME"
    AVERTISSEMENT = "AVERTISSEMENT"
    CRITIQUE = "CRITIQUE"


class ComplianceCheck(BaseModel):
    id: str
    name: str
    status: RiskLevel
    message: str
    reference: str
    url: str
    recommendation: str
    highlight_text: Optional[str] = None


class AnalysisRequest(BaseModel):
    text: str
    url: Optional[str] = None


class AnalysisResponse(BaseModel):
    overall_status: RiskLevel
    risk_score: int  # 0-100, where 100 is highest risk
    completeness_score: int  # 0-100
    checks: List[ComplianceCheck]
    anonymized_text: str
    summary: str


# Legal Knowledge Base (Simulated RAG retrieval)
LEGAL_KNOWLEDGE = {
    "LICO": {
        "rule": "R179(b)",
        "description": "Low Income Cut-Off - Seuil de suffisance financière",
        "thresholds": {
            1: 20635,  # 1 person
            2: 25690,
            3: 31583,
            4: 38346,
            5: 43492,
            6: 49051,
            7: 54610
        },
        "url": "https://laws-lois.justice.gc.ca/fra/reglements/DORS-2002-227/page-22.html"
    },
    "DOCUMENT_VALIDITY": {
        "rule": "R54",
        "description": "Les documents doivent être datés de moins de 6 mois",
        "max_age_days": 180,
        "url": "https://laws-lois.justice.gc.ca/fra/reglements/DORS-2002-227/page-8.html"
    },
    "IDENTITY_VERIFICATION": {
        "rule": "R52",
        "description": "Vérification obligatoire de l'identité du demandeur",
        "required_fields": ["nom", "name", "date de naissance", "dob", "pays", "country"],
        "url": "https://laws-lois.justice.gc.ca/fra/reglements/DORS-2002-227/page-7.html"
    },
    "PROOF_OF_FUNDS": {
        "rule": "R76(1)",
        "description": "Preuve de fonds requise - relevé bancaire certifié",
        "required_keywords": ["relevé", "bancaire", "bank statement", "certifié", "certified"],
        "url": "https://laws-lois.justice.gc.ca/fra/reglements/DORS-2002-227/page-10.html"
    }
}


def anonymize_text(text: str) -> str:
    """
    Anonymize PII using Microsoft Presidio-style patterns
    """
    anonymized = text
    
    # Person names (common pattern after indicators)
    name_patterns = [
        (r"(Nom complet\s*:\s*)([A-Z][a-zéèêëàâ]+\s+[A-Z][a-zéèêëàâ]+)", r"\1<PERSON>"),
        (r"(Demandeur\s*:\s*)([A-Z][a-zéèêëàâ]+\s+[A-Z][a-zéèêëàâ]+)", r"\1<PERSON>"),
        (r"(Name\s*:\s*)([A-Z][a-z]+\s+[A-Z][a-z]+)", r"\1<PERSON>"),
    ]
    for pattern, replacement in name_patterns:
        anonymized = re.sub(pattern, replacement, anonymized)
    
    # Dates (YYYY-MM-DD or DD/MM/YYYY)
    anonymized = re.sub(r"\d{4}-\d{2}-\d{2}", "<DATE_TIME>", anonymized)
    anonymized = re.sub(r"\d{2}/\d{2}/\d{4}", "<DATE_TIME>", anonymized)
    
    # UCI numbers
    anonymized = re.sub(r"UCI[-\s]?\d{8,10}", "<UCI_ID>", anonymized, flags=re.IGNORECASE)
    
    # SIN numbers
    anonymized = re.sub(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b", "<SIN>", anonymized)
    
    # Email
    anonymized = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", anonymized)
    
    # Phone
    anonymized = re.sub(r"\b(\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b", "<PHONE>", anonymized)
    
    # Postal codes
    anonymized = re.sub(r"\b[A-Z]\d[A-Z][-\s]?\d[A-Z]\d\b", "<POSTAL_CODE>", anonymized, flags=re.IGNORECASE)
    
    return anonymized


def extract_income(text: str) -> int:
    """Extract income/balance value from text"""
    # Look for patterns like "5 000 $", "5000$", "$5,000", etc.
    patterns = [
        r"(\d[\d\s]*)\s?\$",  # French format: 5 000 $
        r"\$\s?(\d[\d,]*)",    # English format: $5,000
        r"CAD\s?(\d[\d\s,]*)", # CAD prefix
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            income_str = match.group(1).replace(" ", "").replace(",", "")
            try:
                return int(income_str)
            except ValueError:
                continue
    return 0


def extract_date(text: str) -> Optional[str]:
    """Extract the most recent date from text"""
    # Look for YYYY-MM-DD format
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
    if dates:
        return max(dates)  # Return most recent
    return None


def check_financial_threshold(text: str, family_size: int = 1) -> ComplianceCheck:
    """Check LICO financial threshold compliance"""
    income = extract_income(text)
    threshold = LEGAL_KNOWLEDGE["LICO"]["thresholds"].get(family_size, 20635)
    
    if income == 0:
        return ComplianceCheck(
            id="LICO_001",
            name="Vérification LICO",
            status=RiskLevel.AVERTISSEMENT,
            message="Impossible de détecter le montant des fonds disponibles.",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['LICO']['rule']}",
            url=LEGAL_KNOWLEDGE["LICO"]["url"],
            recommendation="Vérifier manuellement le relevé bancaire.",
            highlight_text=None
        )
    
    if income < threshold:
        # Find the text to highlight
        income_match = re.search(r"(\d[\d\s]*\s?\$)", text)
        highlight = income_match.group(1) if income_match else None
        
        return ComplianceCheck(
            id="LICO_001",
            name="Vérification LICO",
            status=RiskLevel.CRITIQUE,
            message=f"Solde insuffisant détecté ({income:,} $ < {threshold:,} $).",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['LICO']['rule']}",
            url=LEGAL_KNOWLEDGE["LICO"]["url"],
            recommendation="Demander un co-signataire, des preuves de fonds supplémentaires, ou envisager le rejet.",
            highlight_text=highlight
        )
    
    return ComplianceCheck(
        id="LICO_001",
        name="Vérification LICO",
        status=RiskLevel.CONFORME,
        message=f"Seuil financier respecté ({income:,} $ ≥ {threshold:,} $).",
        reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['LICO']['rule']}",
        url=LEGAL_KNOWLEDGE["LICO"]["url"],
        recommendation="Aucune action requise.",
        highlight_text=None
    )


def check_document_validity(text: str) -> ComplianceCheck:
    """Check if documents are within validity period"""
    from datetime import datetime, timedelta
    
    date_str = extract_date(text)
    
    if not date_str:
        return ComplianceCheck(
            id="DOC_001",
            name="Validité des documents",
            status=RiskLevel.AVERTISSEMENT,
            message="Aucune date de document détectée.",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
            url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
            recommendation="Vérifier manuellement la date des documents.",
            highlight_text=None
        )
    
    try:
        doc_date = datetime.strptime(date_str, "%Y-%m-%d")
        max_age = timedelta(days=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["max_age_days"])
        cutoff_date = datetime.now() - max_age
        
        if doc_date < cutoff_date:
            return ComplianceCheck(
                id="DOC_001",
                name="Validité des documents",
                status=RiskLevel.CRITIQUE,
                message=f"Document périmé (daté du {date_str}, > 6 mois).",
                reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
                url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
                recommendation="Demander des documents mis à jour datant de moins de 6 mois.",
                highlight_text=date_str
            )
        
        return ComplianceCheck(
            id="DOC_001",
            name="Validité des documents",
            status=RiskLevel.CONFORME,
            message=f"Documents dans la période de validité ({date_str}).",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
            url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
            recommendation="Aucune action requise.",
            highlight_text=None
        )
    except ValueError:
        return ComplianceCheck(
            id="DOC_001",
            name="Validité des documents",
            status=RiskLevel.AVERTISSEMENT,
            message="Format de date non reconnu.",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
            url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
            recommendation="Vérifier manuellement la date des documents.",
            highlight_text=None
        )


def check_identity_fields(text: str) -> ComplianceCheck:
    """Check if required identity fields are present"""
    text_lower = text.lower()
    required = LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["required_fields"]
    
    found = []
    missing = []
    
    for field in required:
        if field.lower() in text_lower:
            found.append(field)
        else:
            missing.append(field)
    
    completeness = len(found) / len(required) * 100
    
    if completeness >= 80:
        return ComplianceCheck(
            id="ID_001",
            name="Vérification d'identité",
            status=RiskLevel.CONFORME,
            message=f"Informations d'identité complètes ({int(completeness)}%).",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['IDENTITY_VERIFICATION']['rule']}",
            url=LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["url"],
            recommendation="Aucune action requise.",
            highlight_text=None
        )
    elif completeness >= 50:
        return ComplianceCheck(
            id="ID_001",
            name="Vérification d'identité",
            status=RiskLevel.AVERTISSEMENT,
            message=f"Informations d'identité partielles ({int(completeness)}%).",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['IDENTITY_VERIFICATION']['rule']}",
            url=LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["url"],
            recommendation=f"Éléments potentiellement manquants: {', '.join(missing[:3])}.",
            highlight_text=None
        )
    else:
        return ComplianceCheck(
            id="ID_001",
            name="Vérification d'identité",
            status=RiskLevel.CRITIQUE,
            message=f"Informations d'identité insuffisantes ({int(completeness)}%).",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['IDENTITY_VERIFICATION']['rule']}",
            url=LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["url"],
            recommendation=f"Demander les informations manquantes: {', '.join(missing)}.",
            highlight_text=None
        )


def check_proof_of_funds(text: str) -> ComplianceCheck:
    """Check if proper proof of funds documentation is mentioned"""
    text_lower = text.lower()
    keywords = LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["required_keywords"]
    
    found = [kw for kw in keywords if kw.lower() in text_lower]
    
    if len(found) >= 2:
        return ComplianceCheck(
            id="POF_001",
            name="Preuve de fonds",
            status=RiskLevel.CONFORME,
            message="Type de preuve de fonds accepté détecté.",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['PROOF_OF_FUNDS']['rule']}",
            url=LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["url"],
            recommendation="Aucune action requise.",
            highlight_text=None
        )
    elif len(found) >= 1:
        return ComplianceCheck(
            id="POF_001",
            name="Preuve de fonds",
            status=RiskLevel.AVERTISSEMENT,
            message="Type de preuve de fonds partiellement identifié.",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['PROOF_OF_FUNDS']['rule']}",
            url=LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["url"],
            recommendation="Confirmer que le relevé est certifié par l'institution financière.",
            highlight_text=None
        )
    else:
        return ComplianceCheck(
            id="POF_001",
            name="Preuve de fonds",
            status=RiskLevel.CRITIQUE,
            message="Aucune preuve de fonds acceptable détectée.",
            reference=f"Loi sur l'immigration, Article {LEGAL_KNOWLEDGE['PROOF_OF_FUNDS']['rule']}",
            url=LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["url"],
            recommendation="Demander un relevé bancaire certifié des 6 derniers mois.",
            highlight_text=None
        )


def calculate_risk_score(checks: List[ComplianceCheck]) -> int:
    """Calculate overall risk score (0-100)"""
    if not checks:
        return 0
    
    score = 0
    for check in checks:
        if check.status == RiskLevel.CRITIQUE:
            score += 40
        elif check.status == RiskLevel.AVERTISSEMENT:
            score += 15
    
    return min(score, 100)


def calculate_completeness(checks: List[ComplianceCheck]) -> int:
    """Calculate document completeness score (0-100)"""
    if not checks:
        return 0
    
    conforme_count = sum(1 for c in checks if c.status == RiskLevel.CONFORME)
    return int((conforme_count / len(checks)) * 100)


def determine_overall_status(checks: List[ComplianceCheck]) -> RiskLevel:
    """Determine overall compliance status"""
    has_critique = any(c.status == RiskLevel.CRITIQUE for c in checks)
    has_warning = any(c.status == RiskLevel.AVERTISSEMENT for c in checks)
    
    if has_critique:
        return RiskLevel.CRITIQUE
    elif has_warning:
        return RiskLevel.AVERTISSEMENT
    return RiskLevel.CONFORME


def generate_summary(checks: List[ComplianceCheck], overall_status: RiskLevel) -> str:
    """Generate a human-readable summary"""
    critique_checks = [c for c in checks if c.status == RiskLevel.CRITIQUE]
    warning_checks = [c for c in checks if c.status == RiskLevel.AVERTISSEMENT]
    
    if overall_status == RiskLevel.CONFORME:
        return "Tous les contrôles de conformité sont satisfaits. Le dossier peut être traité."
    elif overall_status == RiskLevel.CRITIQUE:
        issues = [c.name for c in critique_checks]
        return f"Problèmes critiques détectés: {', '.join(issues)}. Action immédiate requise."
    else:
        issues = [c.name for c in warning_checks]
        return f"Points d'attention: {', '.join(issues)}. Vérification manuelle recommandée."


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Main analysis endpoint - performs multi-rule compliance checking
    """
    # 1. Anonymize for logging/audit
    safe_text = anonymize_text(request.text)
    
    # 2. Run all compliance checks
    checks = [
        check_financial_threshold(request.text),
        check_document_validity(request.text),
        check_identity_fields(request.text),
        check_proof_of_funds(request.text)
    ]
    
    # 3. Calculate scores
    risk_score = calculate_risk_score(checks)
    completeness_score = calculate_completeness(checks)
    overall_status = determine_overall_status(checks)
    summary = generate_summary(checks, overall_status)
    
    return AnalysisResponse(
        overall_status=overall_status,
        risk_score=risk_score,
        completeness_score=completeness_score,
        checks=checks,
        anonymized_text=safe_text,
        summary=summary
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OLI Backend"}


@app.get("/rules")
async def list_rules():
    """List available compliance rules"""
    return {
        "rules": [
            {"id": "LICO", "name": "Financial Threshold (LICO)", "description": LEGAL_KNOWLEDGE["LICO"]["description"]},
            {"id": "DOC_VALIDITY", "name": "Document Validity", "description": LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["description"]},
            {"id": "ID_VERIFY", "name": "Identity Verification", "description": LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["description"]},
            {"id": "PROOF_FUNDS", "name": "Proof of Funds", "description": LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["description"]}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
