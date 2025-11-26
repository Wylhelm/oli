"""
OLI Compliance Chain
Full pipeline: Anonymization (Presidio) -> RAG -> LLM -> Parsing
"""

import json
import re
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from .ollama_client import OllamaClient, get_ollama_client
from .prompts import (
    COMPLIANCE_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_check_prompt
)

# Import from parent package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.retriever import ContextualRetriever

# Type hint for Presidio anonymizer
if TYPE_CHECKING:
    from anonymization.presidio_anonymizer import PresidioAnonymizer


@dataclass
class ComplianceCheck:
    """Single compliance check result"""
    id: str
    name: str
    status: str  # CONFORME, AVERTISSEMENT, CRITIQUE
    message: str
    reference: str
    url: str
    recommendation: str
    highlight_text: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ComplianceAnalysis:
    """Full compliance analysis result"""
    overall_status: str
    risk_score: int
    completeness_score: int
    checks: list[ComplianceCheck] = field(default_factory=list)
    summary: str = ""
    sources: list[dict] = field(default_factory=list)
    anonymized_text: str = ""
    llm_raw_response: str = ""


class ComplianceChain:
    """
    Full compliance analysis pipeline
    
    Steps:
    1. Anonymize document text (Microsoft Presidio)
    2. Retrieve relevant legal context (RAG)
    3. Generate analysis with LLM
    4. Parse and structure response
    """
    
    def __init__(
        self,
        retriever: ContextualRetriever,
        llm_client: Optional[OllamaClient] = None,
        anonymizer: Optional["PresidioAnonymizer"] = None
    ):
        self.retriever = retriever
        self.llm = llm_client or get_ollama_client()
        self.anonymizer = anonymizer
        
        # Log anonymizer status
        if self.anonymizer:
            status = "Presidio (NER)" if self.anonymizer.is_available() else "Presidio (regex fallback)"
            print(f"[OLI ComplianceChain] Using {status} for anonymization")
        else:
            print("[OLI ComplianceChain] Using basic regex anonymization")
    
    def _anonymize_document(self, document_text: str) -> str:
        """
        Anonymize document using Presidio or fallback
        
        Args:
            document_text: Text to anonymize
            
        Returns:
            Anonymized text
        """
        if self.anonymizer:
            try:
                return self.anonymizer.anonymize(document_text)
            except Exception as e:
                print(f"[OLI] Presidio anonymization failed: {e}, using fallback")
                return self._basic_anonymize(document_text)
        return self._basic_anonymize(document_text)
    
    def analyze(
        self,
        document_text: str,
        url: Optional[str] = None
    ) -> ComplianceAnalysis:
        """
        Run full compliance analysis (synchronous)
        
        Args:
            document_text: The document text to analyze
            url: Optional URL of the document source
        
        Returns:
            ComplianceAnalysis with all checks and recommendations
        """
        # 1. Anonymize with Presidio (or fallback)
        anonymized = self._anonymize_document(document_text)
        
        # 2. Get comprehensive RAG context
        rag_results = self.retriever.retrieve_comprehensive(anonymized)
        
        # Combine all contexts
        all_context = []
        all_sources = []
        for check_type, result in rag_results.items():
            all_context.append(f"## {check_type}\n{result.context}")
            all_sources.extend(result.sources)
        
        combined_context = "\n\n".join(all_context)
        unique_sources = self._dedupe_sources(all_sources)
        
        # 3. Generate LLM analysis using chat API
        prompt = build_analysis_prompt(
            document_text=anonymized,
            legal_context=combined_context,
            sources=unique_sources
        )
        
        try:
            # Use chat method for cloud models compatibility
            messages = [
                {"role": "system", "content": COMPLIANCE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = self.llm.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=4096
            )
            
            # 4. Parse response
            analysis = self._parse_llm_response(response.content)
            analysis.sources = unique_sources
            analysis.anonymized_text = anonymized
            analysis.llm_raw_response = response.content
            
            return analysis
            
        except Exception as e:
            # Fallback to rule-based analysis on LLM failure
            print(f"[OLI] LLM analysis failed: {e}, falling back to rule-based")
            return self._fallback_analysis(document_text, unique_sources)
    
    async def analyze_async(
        self,
        document_text: str,
        url: Optional[str] = None
    ) -> ComplianceAnalysis:
        """
        Run full compliance analysis (asynchronous)
        """
        # 1. Anonymize with Presidio (or fallback)
        anonymized = self._anonymize_document(document_text)
        
        # 2. Get RAG context
        rag_results = self.retriever.retrieve_comprehensive(anonymized)
        
        all_context = []
        all_sources = []
        for check_type, result in rag_results.items():
            all_context.append(f"## {check_type}\n{result.context}")
            all_sources.extend(result.sources)
        
        combined_context = "\n\n".join(all_context)
        unique_sources = self._dedupe_sources(all_sources)
        
        # 3. Generate LLM analysis using chat API
        prompt = build_analysis_prompt(
            document_text=anonymized,
            legal_context=combined_context,
            sources=unique_sources
        )
        
        try:
            # Use chat method for cloud models compatibility
            messages = [
                {"role": "system", "content": COMPLIANCE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = await self.llm.chat_async(
                messages=messages,
                temperature=0.1,
                max_tokens=4096
            )
            
            # 4. Parse response
            analysis = self._parse_llm_response(response.content)
            analysis.sources = unique_sources
            analysis.anonymized_text = anonymized
            analysis.llm_raw_response = response.content
            
            return analysis
            
        except Exception as e:
            print(f"[OLI] LLM analysis failed: {e}, falling back to rule-based")
            return self._fallback_analysis(document_text, unique_sources)
    
    def analyze_single_check(
        self,
        document_text: str,
        check_type: str
    ) -> ComplianceCheck:
        """
        Run a single compliance check with LLM
        
        Args:
            document_text: The document text
            check_type: LICO, DOCUMENT_VALIDITY, IDENTITY, or PROOF_OF_FUNDS
        
        Returns:
            Single ComplianceCheck result
        """
        # Get specific RAG context
        rag_result = self.retriever.retrieve_for_check(check_type, document_text)
        
        # Build check-specific prompt
        prompt = build_check_prompt(
            check_type=check_type,
            document_text=document_text,
            legal_context=rag_result.context
        )
        
        try:
            # Use chat method for cloud models compatibility
            messages = [
                {"role": "system", "content": COMPLIANCE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            response = self.llm.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )
            
            # Parse single check response
            return self._parse_single_check(response.content, check_type)
            
        except Exception as e:
            print(f"[OLI] Single check failed: {e}")
            return ComplianceCheck(
                id=f"{check_type}_001",
                name=check_type,
                status="AVERTISSEMENT",
                message=f"Analyse LLM non disponible: {str(e)}",
                reference="N/A",
                url="",
                recommendation="Vérification manuelle requise",
                confidence=0.0
            )
    
    def _parse_llm_response(self, response: str) -> ComplianceAnalysis:
        """Parse LLM JSON response into ComplianceAnalysis"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_match.group())
            
            checks = []
            for check_data in data.get("checks", []):
                checks.append(ComplianceCheck(
                    id=check_data.get("id", "UNKNOWN"),
                    name=check_data.get("name", "Unknown Check"),
                    status=check_data.get("status", "AVERTISSEMENT"),
                    message=check_data.get("message", ""),
                    reference=check_data.get("reference", ""),
                    url=check_data.get("url", ""),
                    recommendation=check_data.get("recommendation", ""),
                    highlight_text=check_data.get("highlight_text"),
                    confidence=check_data.get("confidence", 0.0)
                ))
            
            return ComplianceAnalysis(
                overall_status=data.get("overall_status", "AVERTISSEMENT"),
                risk_score=data.get("risk_score", 50),
                completeness_score=data.get("completeness_score", 50),
                checks=checks,
                summary=data.get("summary", "Analyse complétée")
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[OLI] Failed to parse LLM response: {e}")
            # Return a default analysis
            return ComplianceAnalysis(
                overall_status="AVERTISSEMENT",
                risk_score=50,
                completeness_score=50,
                checks=[],
                summary="Analyse LLM non parseable, vérification manuelle requise"
            )
    
    def _parse_single_check(self, response: str, check_type: str) -> ComplianceCheck:
        """Parse single check JSON response"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError("No JSON found")
            
            data = json.loads(json_match.group())
            check_data = data.get("check", data)
            
            return ComplianceCheck(
                id=check_data.get("id", f"{check_type}_001"),
                name=check_data.get("name", check_type),
                status=check_data.get("status", "AVERTISSEMENT"),
                message=check_data.get("message", ""),
                reference=check_data.get("reference", ""),
                url=check_data.get("url", ""),
                recommendation=check_data.get("recommendation", ""),
                highlight_text=check_data.get("highlight_text"),
                confidence=check_data.get("confidence", 0.0)
            )
            
        except Exception as e:
            return ComplianceCheck(
                id=f"{check_type}_001",
                name=check_type,
                status="AVERTISSEMENT",
                message=f"Erreur de parsing: {str(e)}",
                reference="",
                url="",
                recommendation="Vérification manuelle requise",
                confidence=0.0
            )
    
    def _basic_anonymize(self, text: str) -> str:
        """Basic anonymization without Presidio"""
        anonymized = text
        
        # Names after indicators
        patterns = [
            (r"(Nom complet\s*:\s*)([A-Z][a-zéèêëàâ]+\s+[A-Z][a-zéèêëàâ]+)", r"\1<PERSON>"),
            (r"(Demandeur\s*:\s*)([A-Z][a-zéèêëàâ]+\s+[A-Z][a-zéèêëàâ]+)", r"\1<PERSON>"),
        ]
        for pattern, replacement in patterns:
            anonymized = re.sub(pattern, replacement, anonymized)
        
        # UCI, SIN, etc.
        anonymized = re.sub(r"UCI[-\s]?\d{8,10}", "<UCI>", anonymized, flags=re.IGNORECASE)
        anonymized = re.sub(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b", "<SIN>", anonymized)
        anonymized = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", anonymized)
        
        return anonymized
    
    def _dedupe_sources(self, sources: list[dict]) -> list[dict]:
        """Remove duplicate sources"""
        seen = set()
        unique = []
        for src in sources:
            url = src.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(src)
        return unique
    
    def _fallback_analysis(
        self,
        document_text: str,
        sources: list[dict]
    ) -> ComplianceAnalysis:
        """Fallback rule-based analysis when LLM fails"""
        checks = []
        
        # Basic LICO check
        income_match = re.search(r"(\d[\d\s]*)\s?\$", document_text)
        if income_match:
            income = int(income_match.group(1).replace(" ", ""))
            threshold = 20635
            
            if income < threshold:
                checks.append(ComplianceCheck(
                    id="LICO_001",
                    name="Vérification LICO",
                    status="CRITIQUE",
                    message=f"Solde insuffisant ({income:,}$ < {threshold:,}$)",
                    reference="RIPR R179(b)",
                    url="https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/",
                    recommendation="Demander des preuves de fonds supplémentaires",
                    highlight_text=income_match.group(0),
                    confidence=0.8
                ))
            else:
                checks.append(ComplianceCheck(
                    id="LICO_001",
                    name="Vérification LICO",
                    status="CONFORME",
                    message=f"Seuil financier respecté ({income:,}$ >= {threshold:,}$)",
                    reference="RIPR R179(b)",
                    url="https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/",
                    recommendation="Aucune action requise",
                    confidence=0.8
                ))
        
        # Determine overall status
        has_critique = any(c.status == "CRITIQUE" for c in checks)
        has_warning = any(c.status == "AVERTISSEMENT" for c in checks)
        
        return ComplianceAnalysis(
            overall_status="CRITIQUE" if has_critique else ("AVERTISSEMENT" if has_warning else "CONFORME"),
            risk_score=60 if has_critique else (30 if has_warning else 10),
            completeness_score=len([c for c in checks if c.status == "CONFORME"]) * 25,
            checks=checks,
            summary="Analyse par règles (LLM non disponible)",
            sources=sources,
            anonymized_text=self._basic_anonymize(document_text)
        )


# Factory function
def create_compliance_chain(retriever: ContextualRetriever) -> ComplianceChain:
    """Create a compliance chain with default settings"""
    return ComplianceChain(retriever=retriever)

