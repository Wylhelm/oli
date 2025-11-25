"""
OLI Prompt Templates
Structured prompts for compliance analysis with RAG context
"""

# System prompt for compliance analysis
COMPLIANCE_SYSTEM_PROMPT = """Tu es OLI (Overlay Legal Intelligence), un assistant d'analyse de conformité réglementaire pour les agents de la fonction publique canadienne.

## Ton rôle:
- Analyser les documents soumis pour détecter les non-conformités avec la législation canadienne
- Croiser les informations du document avec le contexte légal fourni
- Fournir des recommandations claires et actionnables
- Toujours citer les références légales exactes

## Règles importantes:
1. Base tes analyses UNIQUEMENT sur le contexte légal fourni
2. Cite les articles de loi spécifiques (ex: R179, R52, R76)
3. Fournis les URLs vers les sources officielles quand disponibles
4. Sois précis sur les seuils numériques (LICO, délais, etc.)
5. Donne un niveau de confiance honnête pour chaque vérification

## Format de réponse:
Tu dois répondre en JSON valide avec la structure suivante:
{
  "checks": [
    {
      "id": "CHECK_ID",
      "name": "Nom du contrôle",
      "status": "CONFORME|AVERTISSEMENT|CRITIQUE",
      "message": "Description détaillée du résultat",
      "reference": "Article de loi (ex: RIPR R179(b))",
      "url": "URL vers la source officielle",
      "recommendation": "Action recommandée",
      "highlight_text": "Texte exact à surligner dans le document (ou null)",
      "confidence": 0.95
    }
  ],
  "summary": "Résumé en une phrase du statut global",
  "risk_score": 0-100,
  "completeness_score": 0-100,
  "overall_status": "CONFORME|AVERTISSEMENT|CRITIQUE"
}"""


# Template for compliance analysis with RAG context
COMPLIANCE_ANALYSIS_TEMPLATE = """## Document à analyser:
{document_text}

## Contexte légal pertinent (extrait de la législation canadienne):
{legal_context}

## Sources légales disponibles:
{sources}

## Instructions:
1. Analyse le document ci-dessus en utilisant le contexte légal fourni
2. Vérifie les points suivants:
   - LICO: Les fonds disponibles respectent-ils le seuil minimum requis?
   - Validité des documents: Les dates sont-elles conformes (moins de 6 mois)?
   - Identité: Les informations d'identité sont-elles complètes?
   - Preuve de fonds: Le type de document est-il acceptable?
3. Pour chaque vérification, cite la référence légale exacte du contexte fourni
4. Retourne ta réponse en JSON valide

## Réponse (JSON uniquement):"""


# Template for specific check types
CHECK_SPECIFIC_TEMPLATES = {
    "LICO": """## Vérification LICO (Low Income Cut-Off)

Document:
{document_text}

Contexte légal sur les seuils LICO:
{legal_context}

Instructions:
1. Identifie le montant des fonds mentionné dans le document
2. Compare avec les seuils LICO du contexte légal
3. Tiens compte de la taille de la famille si mentionnée
4. Cite l'article exact (R179, etc.)

Réponds en JSON:
{{"check": {{"id": "LICO_001", "name": "Vérification LICO", "status": "...", "message": "...", "reference": "...", "url": "...", "recommendation": "...", "highlight_text": "...", "confidence": 0.0}}}}""",

    "DOCUMENT_VALIDITY": """## Vérification de la validité des documents

Document:
{document_text}

Contexte légal sur la validité:
{legal_context}

Instructions:
1. Identifie les dates mentionnées dans le document
2. Vérifie si les documents ont moins de 6 mois
3. Cite les articles pertinents

Réponds en JSON:
{{"check": {{"id": "DOC_001", "name": "Validité des documents", "status": "...", "message": "...", "reference": "...", "url": "...", "recommendation": "...", "highlight_text": "...", "confidence": 0.0}}}}""",

    "IDENTITY": """## Vérification d'identité

Document:
{document_text}

Contexte légal sur l'identité:
{legal_context}

Instructions:
1. Vérifie la présence des informations d'identité requises
2. Identifie les éléments manquants
3. Cite les articles R52 et connexes

Réponds en JSON:
{{"check": {{"id": "ID_001", "name": "Vérification d'identité", "status": "...", "message": "...", "reference": "...", "url": "...", "recommendation": "...", "highlight_text": null, "confidence": 0.0}}}}""",

    "PROOF_OF_FUNDS": """## Vérification de la preuve de fonds

Document:
{document_text}

Contexte légal sur les preuves de fonds:
{legal_context}

Instructions:
1. Identifie le type de preuve de fonds (relevé bancaire, etc.)
2. Vérifie si c'est un type accepté selon le contexte légal
3. Cite l'article R76 et connexes

Réponds en JSON:
{{"check": {{"id": "POF_001", "name": "Preuve de fonds", "status": "...", "message": "...", "reference": "...", "url": "...", "recommendation": "...", "highlight_text": null, "confidence": 0.0}}}}"""
}


def format_sources(sources: list[dict]) -> str:
    """Format sources list for prompt"""
    if not sources:
        return "Aucune source spécifique disponible"
    
    lines = []
    for i, src in enumerate(sources, 1):
        title = src.get("title", "Document inconnu")
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
        document_text=document_text[:3000],  # Limit document size
        legal_context=legal_context[:4000],  # Limit context size
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

