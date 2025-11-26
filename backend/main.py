from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import re
import os
from enum import Enum

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# RAG imports
from rag.vector_store import LegalVectorStore
from rag.retriever import ContextualRetriever

# LLM imports
from llm.ollama_client import OllamaClient
from llm.compliance_chain import ComplianceChain

# Anonymization imports (Microsoft Presidio)
from anonymization.presidio_anonymizer import PresidioAnonymizer, get_anonymizer

# Global instances (initialized on startup)
vector_store: Optional[LegalVectorStore] = None
retriever: Optional[ContextualRetriever] = None
llm_client: Optional[OllamaClient] = None
compliance_chain: Optional[ComplianceChain] = None
presidio_anonymizer: Optional[PresidioAnonymizer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG, LLM, and Presidio systems on startup"""
    global vector_store, retriever, llm_client, compliance_chain, presidio_anonymizer
    
    # Initialize Presidio Anonymizer
    print("[OLI] Initializing Microsoft Presidio Anonymizer...")
    try:
        # Force new instance to pick up latest configuration
        presidio_anonymizer = get_anonymizer(languages=["en", "fr"], force_new=True)
        if presidio_anonymizer.is_available():
            print(f"[OLI] Presidio Anonymizer ready (with spaCy NER) - Languages: {presidio_anonymizer.languages}")
        else:
            print("[OLI] Presidio running in fallback mode (regex-based)")
    except Exception as e:
        print(f"[OLI] Presidio initialization failed: {e}")
        presidio_anonymizer = None
    
    # Initialize RAG
    print("[OLI] Initializing RAG System...")
    try:
        vector_store = LegalVectorStore()
        retriever = ContextualRetriever(vector_store)
        stats = vector_store.get_stats()
        total_docs = sum(s["count"] for s in stats.values())
        print(f"[OLI] RAG System ready: {total_docs} documents indexed")
    except Exception as e:
        print(f"[OLI] RAG System initialization failed: {e}")
    
    # Initialize LLM
    import os
    ollama_model = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    print(f"[OLI] Initializing LLM (Ollama: {ollama_model})...")
    try:
        llm_client = OllamaClient(model=ollama_model)
        if llm_client.is_available():
            print(f"[OLI] LLM model found: {llm_client.model}")
            # Create compliance chain with Presidio anonymizer
            if retriever:
                compliance_chain = ComplianceChain(
                    retriever=retriever, 
                    llm_client=llm_client,
                    anonymizer=presidio_anonymizer
                )
                print("[OLI] Compliance Chain ready (RAG + LLM + Presidio)")
        else:
            available = llm_client.list_models()
            print(f"[OLI] LLM model not found. Available: {available}")
            print("[OLI] Falling back to rule-based analysis")
    except Exception as e:
        print(f"[OLI] LLM init error: {e}")
        print("[OLI] Falling back to rule-based analysis")
    
    yield
    
    # Cleanup
    if llm_client:
        llm_client.close()
    print("[OLI] Shutting down...")


app = FastAPI(
    title="OLI Backend API",
    description="Overlay Legal Intelligence - Compliance Analysis Engine with RAG",
    version="2.0.0",
    lifespan=lifespan
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
        "description": "Low Income Cut-Off - Financial sufficiency threshold",
        "thresholds": {
            1: 20635,  # 1 person
            2: 25690,
            3: 31583,
            4: 38346,
            5: 43492,
            6: 49051,
            7: 54610
        },
        "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-22.html"
    },
    "DOCUMENT_VALIDITY": {
        "rule": "R54",
        "description": "Documents must be dated within 6 months",
        "max_age_days": 180,
        "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-8.html"
    },
    "IDENTITY_VERIFICATION": {
        "rule": "R52",
        "description": "Mandatory identity verification of the applicant",
        "required_fields": ["nom", "name", "date de naissance", "dob", "pays", "country"],
        "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-7.html"
    },
    "PROOF_OF_FUNDS": {
        "rule": "R76(1)",
        "description": "Proof of funds required - certified bank statement",
        "required_keywords": ["relevé", "bancaire", "bank statement", "certifié", "certified"],
        "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-10.html"
    }
}


def anonymize_text(text: str) -> str:
    """
    Anonymize PII using Microsoft Presidio
    Falls back to regex if Presidio is unavailable
    """
    global presidio_anonymizer
    
    # Use Presidio if available
    if presidio_anonymizer:
        return presidio_anonymizer.anonymize(text)
    
    # Fallback to basic regex anonymization
    anonymized = text
    
    # Person names (common pattern after indicators)
    name_patterns = [
        (r"(Nom complet\s*:\s*)([A-Z][a-zéèêëàâ]+\s+[A-Z][a-zéèêëàâ]+)", r"\1<PERSON>"),
        (r"(Demandeur\s*:\s*)([A-Z][a-zéèêëàâ]+\s+[A-Z][a-zéèêëàâ]+)", r"\1<PERSON>"),
        (r"(Full Name\s*:\s*)([A-Z][a-z]+\s+[A-Z][a-z]+)", r"\1<PERSON>"),
        (r"(Name\s*:\s*)([A-Z][a-z]+\s+[A-Z][a-z]+)", r"\1<PERSON>"),
    ]
    for pattern, replacement in name_patterns:
        anonymized = re.sub(pattern, replacement, anonymized)
    
    # UCI numbers
    anonymized = re.sub(r"UCI[-\s]?\d{8,10}", "<UCI>", anonymized, flags=re.IGNORECASE)
    
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
            name="LICO Verification",
            status=RiskLevel.AVERTISSEMENT,
            message="Unable to detect available funds amount.",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['LICO']['rule']}",
            url=LEGAL_KNOWLEDGE["LICO"]["url"],
            recommendation="Manually verify the bank statement.",
            highlight_text=None
        )
    
    if income < threshold:
        # Find the text to highlight
        income_match = re.search(r"(\d[\d\s]*\s?\$)", text)
        highlight = income_match.group(1) if income_match else None
        
        return ComplianceCheck(
            id="LICO_001",
            name="LICO Verification",
            status=RiskLevel.CRITIQUE,
            message=f"Insufficient balance detected ({income:,} $ < {threshold:,} $).",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['LICO']['rule']}",
            url=LEGAL_KNOWLEDGE["LICO"]["url"],
            recommendation="Request a co-signer, additional proof of funds, or consider rejection.",
            highlight_text=highlight
        )
    
    return ComplianceCheck(
        id="LICO_001",
        name="LICO Verification",
        status=RiskLevel.CONFORME,
        message=f"Financial threshold met ({income:,} $ ≥ {threshold:,} $).",
        reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['LICO']['rule']}",
        url=LEGAL_KNOWLEDGE["LICO"]["url"],
        recommendation="No action required.",
        highlight_text=None
    )


def check_document_validity(text: str) -> ComplianceCheck:
    """Check if documents are within validity period"""
    from datetime import datetime, timedelta
    
    date_str = extract_date(text)
    
    if not date_str:
        return ComplianceCheck(
            id="DOC_001",
            name="Document Validity",
            status=RiskLevel.AVERTISSEMENT,
            message="No document date detected.",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
            url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
            recommendation="Manually verify document dates.",
            highlight_text=None
        )
    
    try:
        doc_date = datetime.strptime(date_str, "%Y-%m-%d")
        max_age = timedelta(days=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["max_age_days"])
        cutoff_date = datetime.now() - max_age
        
        if doc_date < cutoff_date:
            return ComplianceCheck(
                id="DOC_001",
                name="Document Validity",
                status=RiskLevel.CRITIQUE,
                message=f"Expired document (dated {date_str}, > 6 months old).",
                reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
                url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
                recommendation="Request updated documents dated within 6 months.",
                highlight_text=date_str
            )
        
        return ComplianceCheck(
            id="DOC_001",
            name="Document Validity",
            status=RiskLevel.CONFORME,
            message=f"Documents within validity period ({date_str}).",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
            url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
            recommendation="No action required.",
            highlight_text=None
        )
    except ValueError:
        return ComplianceCheck(
            id="DOC_001",
            name="Document Validity",
            status=RiskLevel.AVERTISSEMENT,
            message="Unrecognized date format.",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['DOCUMENT_VALIDITY']['rule']}",
            url=LEGAL_KNOWLEDGE["DOCUMENT_VALIDITY"]["url"],
            recommendation="Manually verify document dates.",
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
            name="Identity Verification",
            status=RiskLevel.CONFORME,
            message=f"Identity information complete ({int(completeness)}%).",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['IDENTITY_VERIFICATION']['rule']}",
            url=LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["url"],
            recommendation="No action required.",
            highlight_text=None
        )
    elif completeness >= 50:
        return ComplianceCheck(
            id="ID_001",
            name="Identity Verification",
            status=RiskLevel.AVERTISSEMENT,
            message=f"Partial identity information ({int(completeness)}%).",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['IDENTITY_VERIFICATION']['rule']}",
            url=LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["url"],
            recommendation=f"Potentially missing elements: {', '.join(missing[:3])}.",
            highlight_text=None
        )
    else:
        return ComplianceCheck(
            id="ID_001",
            name="Identity Verification",
            status=RiskLevel.CRITIQUE,
            message=f"Insufficient identity information ({int(completeness)}%).",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['IDENTITY_VERIFICATION']['rule']}",
            url=LEGAL_KNOWLEDGE["IDENTITY_VERIFICATION"]["url"],
            recommendation=f"Request missing information: {', '.join(missing)}.",
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
            name="Proof of Funds",
            status=RiskLevel.CONFORME,
            message="Accepted proof of funds type detected.",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['PROOF_OF_FUNDS']['rule']}",
            url=LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["url"],
            recommendation="No action required.",
            highlight_text=None
        )
    elif len(found) >= 1:
        return ComplianceCheck(
            id="POF_001",
            name="Proof of Funds",
            status=RiskLevel.AVERTISSEMENT,
            message="Proof of funds type partially identified.",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['PROOF_OF_FUNDS']['rule']}",
            url=LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["url"],
            recommendation="Confirm the statement is certified by the financial institution.",
            highlight_text=None
        )
    else:
        return ComplianceCheck(
            id="POF_001",
            name="Proof of Funds",
            status=RiskLevel.CRITIQUE,
            message="No acceptable proof of funds detected.",
            reference=f"Immigration Act, Article {LEGAL_KNOWLEDGE['PROOF_OF_FUNDS']['rule']}",
            url=LEGAL_KNOWLEDGE["PROOF_OF_FUNDS"]["url"],
            recommendation="Request a certified bank statement from the last 6 months.",
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
        return "All compliance checks are satisfied. The file can be processed."
    elif overall_status == RiskLevel.CRITIQUE:
        issues = [c.name for c in critique_checks]
        return f"Critical issues detected: {', '.join(issues)}. Immediate action required."
    else:
        issues = [c.name for c in warning_checks]
        return f"Points of attention: {', '.join(issues)}. Manual verification recommended."


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
    rag_status = "ready" if vector_store else "unavailable"
    rag_docs = 0
    if vector_store:
        stats = vector_store.get_stats()
        rag_docs = sum(s["count"] for s in stats.values())
    
    # Check Presidio status
    presidio_status = "unavailable"
    if presidio_anonymizer:
        presidio_status = "ready" if presidio_anonymizer.is_available() else "fallback"
    
    return {
        "status": "healthy", 
        "service": "OLI Backend",
        "version": "2.1.0",
        "rag_status": rag_status,
        "rag_documents": rag_docs,
        "presidio_status": presidio_status
    }


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


# ============================================================================
# RAG Endpoints
# ============================================================================

class RAGSearchRequest(BaseModel):
    query: str
    n_results: int = 5
    min_score: float = 0.3


class RAGSearchResult(BaseModel):
    id: str
    text: str
    score: float
    doc_title: str
    doc_type: str
    section: str
    url: str


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResult]
    context: str
    sources: List[dict]


@app.post("/rag/search", response_model=RAGSearchResponse)
async def rag_search(request: RAGSearchRequest):
    """
    Search the legal knowledge base using RAG
    
    Returns relevant legal context from Canadian immigration laws
    """
    if not retriever:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not available. Please ensure vector database is initialized."
        )
    
    result = retriever.retrieve(
        query=request.query,
        n_results=request.n_results,
        min_score=request.min_score
    )
    
    formatted_results = []
    for doc in result.documents:
        metadata = doc.get("metadata", {})
        formatted_results.append(RAGSearchResult(
            id=doc.get("id", ""),
            text=doc.get("text", "")[:500],  # Limit text length in response
            score=doc.get("score", 0),
            doc_title=metadata.get("doc_title", ""),
            doc_type=metadata.get("doc_type", ""),
            section=metadata.get("section", ""),
            url=metadata.get("html_url", "")
        ))
    
    return RAGSearchResponse(
        query=request.query,
        results=formatted_results,
        context=result.context[:2000],  # Limit context length
        sources=result.sources
    )


class RAGContextRequest(BaseModel):
    check_type: str  # LICO, DOCUMENT_VALIDITY, IDENTITY, PROOF_OF_FUNDS
    document_text: Optional[str] = None


@app.post("/rag/context")
async def get_rag_context(request: RAGContextRequest):
    """
    Get relevant legal context for a specific compliance check type
    """
    if not retriever:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not available"
        )
    
    valid_types = ["LICO", "DOCUMENT_VALIDITY", "IDENTITY", "PROOF_OF_FUNDS"]
    if request.check_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid check_type. Must be one of: {valid_types}"
        )
    
    result = retriever.retrieve_for_check(
        check_type=request.check_type,
        document_text=request.document_text or "",
        n_results=5
    )
    
    return {
        "check_type": request.check_type,
        "documents_found": len(result.documents),
        "context": result.context,
        "sources": result.sources,
        "relevance_score": result.total_score
    }


@app.get("/rag/stats")
async def get_rag_stats():
    """Get statistics about the RAG vector store"""
    if not vector_store:
        raise HTTPException(
            status_code=503,
            detail="RAG system not available"
        )
    
    stats = vector_store.get_stats()
    total = sum(s["count"] for s in stats.values())
    
    return {
        "status": "ready",
        "total_documents": total,
        "collections": stats
    }


# ============================================================================
# LLM-Powered Analysis Endpoints
# ============================================================================

class LLMAnalysisRequest(BaseModel):
    text: str
    url: Optional[str] = None
    use_llm: bool = True  # If False, falls back to rule-based


class LLMComplianceCheck(BaseModel):
    id: str
    name: str
    status: str
    message: str
    reference: str
    url: str
    recommendation: str
    highlight_text: Optional[str] = None
    confidence: float = 0.0


class LLMAnalysisResponse(BaseModel):
    overall_status: str
    risk_score: int
    completeness_score: int
    checks: List[LLMComplianceCheck]
    summary: str
    sources: List[dict]
    anonymized_text: str
    analysis_mode: str  # "llm" or "rule-based"


@app.post("/analyze/llm", response_model=LLMAnalysisResponse)
async def analyze_with_llm(request: LLMAnalysisRequest):
    """
    Analyze document using RAG + LLM pipeline
    
    This endpoint uses:
    1. RAG to retrieve relevant legal context from Canadian immigration laws
    2. LLM (Ollama gpt-oss:120b-cloud) to analyze compliance
    3. Structured output with legal citations
    """
    global compliance_chain, llm_client
    
    # Initialize chain on-demand if not ready
    if not compliance_chain and retriever:
        import os
        ollama_model = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        try:
            if not llm_client:
                llm_client = OllamaClient(model=ollama_model)
            if llm_client.is_available():
                compliance_chain = ComplianceChain(retriever=retriever, llm_client=llm_client)
        except Exception as e:
            print(f"[OLI] On-demand chain init failed: {e}")
    
    if not compliance_chain:
        # Fall back to rule-based if LLM not available
        if not request.use_llm:
            raise HTTPException(
                status_code=503,
                detail="LLM not available. Use /analyze for rule-based analysis."
            )
    
    try:
        # Run async analysis
        if compliance_chain:
            result = await compliance_chain.analyze_async(
                document_text=request.text,
                url=request.url
            )
            analysis_mode = "llm"
        else:
            # Fallback to rule-based
            safe_text = anonymize_text(request.text)
            checks = [
                check_financial_threshold(request.text),
                check_document_validity(request.text),
                check_identity_fields(request.text),
                check_proof_of_funds(request.text)
            ]
            
            return LLMAnalysisResponse(
                overall_status=determine_overall_status(checks).value,
                risk_score=calculate_risk_score(checks),
                completeness_score=calculate_completeness(checks),
                checks=[
                    LLMComplianceCheck(
                        id=c.id,
                        name=c.name,
                        status=c.status.value,
                        message=c.message,
                        reference=c.reference,
                        url=c.url,
                        recommendation=c.recommendation,
                        highlight_text=c.highlight_text,
                        confidence=0.9
                    ) for c in checks
                ],
                summary=generate_summary(checks, determine_overall_status(checks)),
                sources=[],
                anonymized_text=safe_text,
                analysis_mode="rule-based"
            )
        
        return LLMAnalysisResponse(
            overall_status=result.overall_status,
            risk_score=result.risk_score,
            completeness_score=result.completeness_score,
            checks=[
                LLMComplianceCheck(
                    id=c.id,
                    name=c.name,
                    status=c.status,
                    message=c.message,
                    reference=c.reference,
                    url=c.url,
                    recommendation=c.recommendation,
                    highlight_text=c.highlight_text,
                    confidence=c.confidence
                ) for c in result.checks
            ],
            summary=result.summary,
            sources=result.sources,
            anonymized_text=result.anonymized_text,
            analysis_mode=analysis_mode
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/llm/status")
async def get_llm_status():
    """Check LLM availability and model info"""
    if not llm_client:
        return {
            "status": "unavailable",
            "message": "LLM client not initialized"
        }
    
    try:
        is_available = llm_client.is_available()
        models = llm_client.list_models()
        
        return {
            "status": "ready" if is_available else "model_not_found",
            "model": llm_client.model,
            "base_url": llm_client.base_url,
            "available_models": models,
            "chain_ready": compliance_chain is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================================
# Anonymization Endpoints (Microsoft Presidio)
# ============================================================================

class AnonymizeRequest(BaseModel):
    text: str
    language: Optional[str] = None  # Auto-detect if not specified
    return_entities: bool = False


class AnonymizeResponse(BaseModel):
    anonymized_text: str
    entities_detected: Optional[List[dict]] = None
    entities_by_type: Optional[dict] = None
    total_entities: int = 0
    presidio_available: bool = False


@app.post("/anonymize", response_model=AnonymizeResponse)
async def anonymize_endpoint(request: AnonymizeRequest):
    """
    Anonymize text using Microsoft Presidio
    
    Replaces PII with tokens:
    - Canadian: SIN (<NAS>), UCI (<UCI>), Postal Code (<CODE_POSTAL>)
    - Standard: Names (<PERSONNE>), Emails (<COURRIEL>), Phones (<TELEPHONE>)
    
    Supports French and English text with automatic language detection.
    """
    global presidio_anonymizer
    
    if not presidio_anonymizer:
        # Fallback to basic anonymization
        return AnonymizeResponse(
            anonymized_text=anonymize_text(request.text),
            total_entities=0,
            presidio_available=False
        )
    
    if request.return_entities:
        result = presidio_anonymizer.anonymize_with_details(request.text, request.language)
        return AnonymizeResponse(
            anonymized_text=result.anonymized_text,
            entities_detected=[e.to_dict() for e in result.entities_detected],
            entities_by_type=result.entities_by_type,
            total_entities=len(result.entities_detected),
            presidio_available=presidio_anonymizer.is_available()
        )
    else:
        anonymized = presidio_anonymizer.anonymize(request.text, request.language)
        return AnonymizeResponse(
            anonymized_text=anonymized,
            presidio_available=presidio_anonymizer.is_available()
        )


@app.post("/anonymize/detect")
async def detect_entities(request: AnonymizeRequest):
    """
    Detect PII entities without anonymizing
    
    Returns list of detected entities with their types, positions, and confidence scores.
    Useful for previewing what would be anonymized.
    """
    global presidio_anonymizer
    
    if not presidio_anonymizer:
        return {
            "error": "Presidio not available",
            "entities": []
        }
    
    entities = presidio_anonymizer.detect_entities(request.text, request.language)
    
    return {
        "text_length": len(request.text),
        "entities": [e.to_dict() for e in entities],
        "total_entities": len(entities),
        "supported_entity_types": presidio_anonymizer.get_supported_entities()
    }


@app.get("/anonymize/status")
async def get_anonymizer_status():
    """Get status of the Presidio anonymizer"""
    global presidio_anonymizer
    
    if not presidio_anonymizer:
        return {
            "status": "unavailable",
            "message": "Presidio anonymizer not initialized",
            "mode": "fallback_regex"
        }
    
    return {
        "status": "ready" if presidio_anonymizer.is_available() else "fallback",
        "mode": "presidio" if presidio_anonymizer.is_available() else "fallback_regex",
        "supported_languages": presidio_anonymizer.languages,
        "supported_entities": presidio_anonymizer.get_supported_entities(),
        "canadian_entities": ["CA_SIN", "CA_POSTAL_CODE", "CA_UCI", "CA_PASSPORT"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
