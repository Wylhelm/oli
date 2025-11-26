"""
OLI Prompt Templates
Structured prompts for compliance analysis with RAG context
All prompts enforce English-only output
"""

# System prompt for compliance analysis
COMPLIANCE_SYSTEM_PROMPT = """You are OLI, an English-speaking compliance analysis assistant for Canadian immigration.

IMPORTANT: You ONLY speak English. All your responses must be in English.

Your role:
- Analyze immigration documents for compliance with Canadian law
- Output structured JSON analysis results
- Write all messages, summaries, and recommendations in English

Check names to use:
- "LICO Financial Threshold"
- "Document Validity"
- "Identity Verification"
- "Proof of Funds Type"

Status values (use these exact English words):
- "COMPLIANT" = passes the check
- "WARNING" = needs attention
- "CRITICAL" = fails the check

CRITICAL RULES:
1. highlight_text MUST be an EXACT copy of text from the document
   - Copy the text exactly as it appears, including symbols like $ and commas
   - Examples: "$5,000", "$35,000", "2024-01-15", "Jean Tremblay"
   - If no specific text to highlight, use null

2. DO NOT HALLUCINATE OR INVENT PROBLEMS:
   - If you see real dates like "1985-04-12" or "2030-05-15", they are VALID dates, not placeholders
   - If you see real names like "Sophie", "Jean-Claude", "Ahmed", they are REAL names, not placeholders
   - Do NOT mention "<DATE>" or "placeholder" unless the field is literally EMPTY or contains that exact text
   - Look for "Form Data" or "Field [...]:" sections - these contain actual user-entered values
   - ONLY flag as WARNING/CRITICAL if data is actually MISSING, INVALID, or EXPIRED

3. Base your analysis ONLY on what's actually in the document
   - Do not assume fields are empty if you see values
   - Do not invent problems that don't exist

Example English messages:
- "The balance of $5,000 is below the required LICO threshold."
- "Documents are dated within the 6-month validity period."
- "All required identity information is present."
- "Request updated bank statements dated within 6 months." """


# Template for compliance analysis with RAG context
COMPLIANCE_ANALYSIS_TEMPLATE = """You are analyzing a Canadian immigration document. Write your analysis in English.

=== DOCUMENT TEXT ===
{document_text}
=== END DOCUMENT ===

=== LEGAL REFERENCE ===
{legal_context}
=== END LEGAL REFERENCE ===

SOURCES: {sources}

ANALYSIS TASKS:
1. LICO Financial Threshold - Check if funds meet minimum ($14,690+ for single applicant)
2. Document Validity - Check if documents are dated within last 6 months
3. Identity Verification - Check if identity information is complete
4. Proof of Funds Type - Check if document type is acceptable (bank statement, etc.)

IMPORTANT - highlight_text rules:
- MUST be an EXACT copy-paste from the DOCUMENT TEXT above
- Include the exact formatting: "$5,000" not "5000" or "5,000 CAD"
- For LICO check: use the balance amount like "$5,000" or "$35,000"
- For Document Validity: use the date like "2024-01-15" or "January 15, 2024"
- For Identity: use the name exactly as written
- If unsure, use null

OUTPUT FORMAT (JSON with English text):
{{
  "checks": [
    {{"id": "LICO_001", "name": "LICO Financial Threshold", "status": "COMPLIANT|WARNING|CRITICAL", "message": "English description", "reference": "IRPR R179", "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/", "recommendation": "English recommendation", "highlight_text": "$5,000", "confidence": 0.95}},
    {{"id": "DOC_001", "name": "Document Validity", "status": "...", "message": "...", "reference": "IRPR Section 44", "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/", "recommendation": "...", "highlight_text": "2024-01-15", "confidence": 0.95}},
    {{"id": "ID_001", "name": "Identity Verification", "status": "...", "message": "...", "reference": "IRPA Section 88", "url": "https://laws-lois.justice.gc.ca/eng/acts/I-2.5/", "recommendation": "...", "highlight_text": null, "confidence": 0.95}},
    {{"id": "POF_001", "name": "Proof of Funds Type", "status": "...", "message": "...", "reference": "IRPR R76", "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/", "recommendation": "...", "highlight_text": null, "confidence": 0.95}}
  ],
  "summary": "One sentence English summary",
  "risk_score": 0-100,
  "completeness_score": 0-100,
  "overall_status": "COMPLIANT|WARNING|CRITICAL"
}}

Your JSON response:"""


# Template for specific check types
CHECK_SPECIFIC_TEMPLATES = {
    "LICO": """Analyze this document for LICO compliance. Respond in English JSON.

DOCUMENT:
{document_text}

LEGAL CONTEXT:
{legal_context}

Check if funds meet LICO threshold ($14,690 for single applicant).
IMPORTANT: highlight_text must be EXACT text from document (e.g. "$5,000" or "$35,000")

JSON format:
{{"check": {{"id": "LICO_001", "name": "LICO Financial Threshold", "status": "COMPLIANT|WARNING|CRITICAL", "message": "English description", "reference": "IRPR R179", "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/", "recommendation": "English recommendation", "highlight_text": "$5,000", "confidence": 0.95}}}}

Your response:""",

    "DOCUMENT_VALIDITY": """Analyze this document for validity. Respond in English JSON.

DOCUMENT:
{document_text}

LEGAL CONTEXT:
{legal_context}

Check if documents are within 6-month validity period.
CRITICAL RULES:
- ONLY flag as WARNING/CRITICAL if actual dates are MISSING or EXPIRED
- If you see real dates in YYYY-MM-DD format (e.g., "1990-07-22", "2030-05-15"), consider them VALID
- Do NOT mention placeholders like <DATE> unless the document literally contains empty fields or placeholder text
- Check "Form Data" section for actual field values

IMPORTANT: highlight_text must be EXACT date from document (e.g. "2024-01-15")

JSON format:
{{"check": {{"id": "DOC_001", "name": "Document Validity", "status": "COMPLIANT|WARNING|CRITICAL", "message": "English description", "reference": "IRPR Section 44", "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/", "recommendation": "English recommendation", "highlight_text": "2024-01-15", "confidence": 0.95}}}}

Your response:""",

    "IDENTITY": """Analyze this document for identity completeness. Respond in English JSON.

DOCUMENT:
{document_text}

LEGAL CONTEXT:
{legal_context}

Check if required identity information is present (name, DOB, citizenship, passport).
CRITICAL RULES:
- ONLY flag as WARNING/CRITICAL if actual data is MISSING or EMPTY
- If you see real dates in YYYY-MM-DD format and real names/passport numbers, consider them VALID
- Do NOT mention placeholders like <DATE> unless fields are literally empty
- Check "Form Data" or "FORM DATA" sections for actual field values
- Names like "Jean-Claude", "Ahmed", dates like "1990-07-22" are REAL data, not placeholders

JSON format:
{{"check": {{"id": "ID_001", "name": "Identity Verification", "status": "COMPLIANT|WARNING|CRITICAL", "message": "English description", "reference": "IRPA Section 88", "url": "https://laws-lois.justice.gc.ca/eng/acts/I-2.5/", "recommendation": "English recommendation", "highlight_text": null, "confidence": 0.95}}}}

Your response:""",

    "PROOF_OF_FUNDS": """Analyze this document for proof of funds type. Respond in English JSON.

DOCUMENT:
{document_text}

LEGAL CONTEXT:
{legal_context}

Check if document is an acceptable proof of funds (certified bank statement, etc.).

JSON format:
{{"check": {{"id": "POF_001", "name": "Proof of Funds Type", "status": "COMPLIANT|WARNING|CRITICAL", "message": "English description", "reference": "IRPR R76", "url": "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/", "recommendation": "English recommendation", "highlight_text": null, "confidence": 0.95}}}}

Your response:"""
}


def format_sources(sources: list[dict]) -> str:
    """Format sources list for prompt"""
    if not sources:
        return "No specific source available"
    
    lines = []
    for i, src in enumerate(sources, 1):
        title = src.get("title", "Unknown document")
        url = src.get("url", "")
        doc_type = src.get("doc_type", "")
        lines.append(f"{i}. {title} ({doc_type})")
        if url:
            lines.append(f"   URL: {url}")
    
    return "\n".join(lines)


def build_analysis_prompt(
    document_text: str,
    legal_context: str,
    sources: list[dict]
) -> str:
    """Build the full analysis prompt"""
    return COMPLIANCE_ANALYSIS_TEMPLATE.format(
        document_text=document_text[:3000],
        legal_context=legal_context[:4000],
        sources=format_sources(sources)
    )


def build_check_prompt(
    check_type: str,
    document_text: str,
    legal_context: str
) -> str:
    """Build a check-specific prompt"""
    template = CHECK_SPECIFIC_TEMPLATES.get(check_type)
    if not template:
        raise ValueError(f"Unknown check type: {check_type}")
    
    return template.format(
        document_text=document_text[:2000],
        legal_context=legal_context[:3000]
    )
