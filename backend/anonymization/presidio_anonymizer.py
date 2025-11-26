"""
OLI Presidio Anonymizer
Advanced PII anonymization using Microsoft Presidio with Canadian-specific recognizers

Supports:
- Canadian Social Insurance Number (SIN/NAS)
- Canadian Postal Codes
- UCI (Unique Client Identifier) for Immigration
- Standard PII: Names, Emails, Phones, Credit Cards, Dates, etc.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re
import logging

# Presidio imports
try:
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logging.warning("[OLI] Presidio not installed. Using basic regex anonymization.")

logger = logging.getLogger(__name__)


@dataclass
class DetectedEntity:
    """Represents a detected PII entity"""
    entity_type: str
    text: str
    start: int
    end: int
    score: float
    
    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "score": self.score
        }


@dataclass
class AnonymizationResult:
    """Result of anonymization operation"""
    original_text: str
    anonymized_text: str
    entities_detected: List[DetectedEntity] = field(default_factory=list)
    entities_by_type: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "anonymized_text": self.anonymized_text,
            "entities_detected": [e.to_dict() for e in self.entities_detected],
            "entities_by_type": self.entities_by_type,
            "total_entities": len(self.entities_detected),
            "success": self.success,
            "error": self.error
        }


class CanadianSINRecognizer(PatternRecognizer):
    """
    Recognizer for Canadian Social Insurance Numbers (SIN/NAS)
    Format: XXX-XXX-XXX or XXX XXX XXX or XXXXXXXXX
    """
    
    PATTERNS = [
        Pattern(
            name="SIN with dashes",
            regex=r"\b\d{3}-\d{3}-\d{3}\b",
            score=0.95  # High score for exact pattern
        ),
        Pattern(
            name="SIN with spaces",
            regex=r"\b\d{3}\s\d{3}\s\d{3}\b",
            score=0.95
        ),
        Pattern(
            name="SIN continuous",
            regex=r"\b\d{9}\b",
            score=0.4  # Lower score as it could be other numbers
        )
    ]
    
    CONTEXT = ["sin", "nas", "social insurance", "numéro d'assurance sociale", 
               "social security", "ssn", "assurance sociale"]
    
    def __init__(self):
        # Don't set supported_language so it works for all languages
        super().__init__(
            supported_entity="CA_SIN",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            name="Canadian SIN Recognizer"
        )


class CanadianPostalCodeRecognizer(PatternRecognizer):
    """
    Recognizer for Canadian Postal Codes
    Format: A1A 1A1 or A1A1A1
    """
    
    PATTERNS = [
        Pattern(
            name="Postal code with space",
            regex=r"\b[A-Za-z]\d[A-Za-z]\s\d[A-Za-z]\d\b",
            score=0.95  # High score for exact Canadian format
        ),
        Pattern(
            name="Postal code without space",
            regex=r"\b[A-Za-z]\d[A-Za-z]\d[A-Za-z]\d\b",
            score=0.95
        )
    ]
    
    CONTEXT = ["postal", "code postal", "zip", "address", "adresse", "qc", "on", "bc", "ab"]
    
    def __init__(self):
        super().__init__(
            supported_entity="CA_POSTAL_CODE",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            name="Canadian Postal Code Recognizer"
        )


class CanadianUCIRecognizer(PatternRecognizer):
    """
    Recognizer for IRCC Unique Client Identifier (UCI)
    Format: UCI-XXXXXXXX or UCI XXXXXXXX (8-10 digits)
    """
    
    PATTERNS = [
        Pattern(
            name="UCI with prefix",
            regex=r"\bUCI[-\s]?\d{8,10}\b",
            score=0.95
        ),
        Pattern(
            name="UCI number only (with context)",
            regex=r"\b\d{8,10}\b",
            score=0.3  # Lower score, needs context
        )
    ]
    
    CONTEXT = ["uci", "client identifier", "identifiant client", "ircc", 
               "immigration", "client id"]
    
    def __init__(self):
        super().__init__(
            supported_entity="CA_UCI",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            name="Canadian UCI Recognizer"
        )


class CanadianPassportRecognizer(PatternRecognizer):
    """
    Recognizer for Canadian Passport Numbers
    Format: 2 letters followed by 6 digits
    """
    
    PATTERNS = [
        Pattern(
            name="Canadian Passport",
            regex=r"\b[A-Z]{2}\d{6}\b",
            score=0.7
        )
    ]
    
    CONTEXT = ["passport", "passeport", "travel document", "document de voyage"]
    
    def __init__(self):
        super().__init__(
            supported_entity="CA_PASSPORT",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            name="Canadian Passport Recognizer"
        )


class CanadianPhoneRecognizer(PatternRecognizer):
    """
    Recognizer for Canadian Phone Numbers
    Various formats supported
    """
    
    PATTERNS = [
        Pattern(
            name="Phone with country code",
            regex=r"\+1[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b",
            score=0.95  # High score for international format
        ),
        Pattern(
            name="Phone standard",
            regex=r"\b\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b",
            score=0.85
        )
    ]
    
    CONTEXT = ["phone", "tel", "telephone", "téléphone", "cell", "mobile", 
               "contact", "call", "appeler", "numéro"]
    
    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            name="Canadian Phone Recognizer"
        )


class BankAccountRecognizer(PatternRecognizer):
    """
    Recognizer for Bank Account Numbers
    Uses context to avoid false positives
    """
    
    PATTERNS = [
        Pattern(
            name="Account number",
            regex=r"\b\d{5,12}\b",
            score=0.3  # Low base score
        )
    ]
    
    CONTEXT = ["account", "compte", "transit", "bank", "banque", "institution",
               "routing", "acheminement"]
    
    def __init__(self):
        super().__init__(
            supported_entity="BANK_ACCOUNT",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            name="Bank Account Recognizer"
        )


class PresidioAnonymizer:
    """
    Microsoft Presidio-based anonymizer with Canadian-specific recognizers
    
    Features:
    - Canadian PII: SIN, Postal Codes, UCI, Passports
    - Standard PII: Names, Emails, Phones, Credit Cards, Dates
    - Bilingual support (French/English)
    - Configurable replacement tokens
    """
    
    # Default replacement operators
    DEFAULT_OPERATORS = {
        "PERSON": "<PERSON>",
        "PHONE_NUMBER": "<PHONE>",
        "EMAIL_ADDRESS": "<EMAIL>",
        "CREDIT_CARD": "<CREDIT_CARD>",
        "DATE_TIME": "<DATE>",
        "LOCATION": "<LOCATION>",
        "IBAN_CODE": "<IBAN>",
        "IP_ADDRESS": "<IP_ADDRESS>",
        "URL": "<URL>",
        # Canadian-specific
        "CA_SIN": "<SIN>",
        "CA_POSTAL_CODE": "<POSTAL_CODE>",
        "CA_UCI": "<UCI>",
        "CA_PASSPORT": "<PASSPORT>",
        "BANK_ACCOUNT": "<BANK_ACCOUNT>",
    }
    
    def __init__(
        self, 
        languages: List[str] = None,
        custom_operators: Dict[str, str] = None,
        score_threshold: float = 0.7  # Increased from 0.5 to reduce false positives
    ):
        """
        Initialize the Presidio anonymizer
        
        Args:
            languages: List of language codes to support (default: ["en", "fr"])
            custom_operators: Custom replacement tokens
            score_threshold: Minimum confidence score for detection (0.7 recommended)
        """
        self.languages = languages or ["en", "fr"]
        self.score_threshold = score_threshold
        self.operators = {**self.DEFAULT_OPERATORS, **(custom_operators or {})}
        
        self._use_presidio = PRESIDIO_AVAILABLE
        self._analyzer = None
        self._anonymizer = None
        self._available_languages = []  # Track which languages actually have spaCy NER models
        
        if self._use_presidio:
            self._initialize_presidio()
        
        if not self._use_presidio:
            logger.warning("[OLI] Presidio not available, using fallback regex anonymization")
    
    def _initialize_presidio(self):
        """Initialize Presidio engines with Canadian recognizers"""
        try:
            # Try to load spaCy models
            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": []
            }
            
            # Check which models are available
            import spacy
            available_models = []
            available_languages = []
            
            # Try English model
            for en_model in ["en_core_web_lg", "en_core_web_md", "en_core_web_sm"]:
                try:
                    spacy.load(en_model)
                    nlp_config["models"].append({"lang_code": "en", "model_name": en_model})
                    available_models.append(en_model)
                    available_languages.append("en")
                    logger.info(f"[OLI] Found English model: {en_model}")
                    break
                except OSError:
                    continue
            
            # Try French model - check all common naming patterns
            french_models = [
                "fr_core_news_lg", "fr_core_news_md", "fr_core_news_sm",
                "fr_dep_news_trf",  # Transformer model
            ]
            for fr_model in french_models:
                try:
                    spacy.load(fr_model)
                    nlp_config["models"].append({"lang_code": "fr", "model_name": fr_model})
                    available_models.append(fr_model)
                    available_languages.append("fr")
                    logger.info(f"[OLI] Found French model: {fr_model}")
                    break
                except OSError as e:
                    logger.debug(f"[OLI] French model {fr_model} not found: {e}")
                    continue
            
            # If French not found, try to detect any French model
            if "fr" not in available_languages:
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", "-m", "spacy", "info", "--json"],
                        capture_output=True, text=True, timeout=10
                    )
                    if "fr_" in result.stdout:
                        logger.warning("[OLI] French spaCy model may be installed but not loading correctly")
                except:
                    pass
            
            if not nlp_config["models"]:
                logger.warning("[OLI] No spaCy models found. Install with: python -m spacy download en_core_web_sm")
                self._use_presidio = False
                return
            
            logger.info(f"[OLI] Using spaCy models: {available_models}")
            
            # Update supported languages to match available models
            self.languages = available_languages
            
            # Create NLP engine
            provider = NlpEngineProvider(nlp_configuration=nlp_config)
            nlp_engine = provider.create_engine()
            
            # Create registry and load ONLY for available languages
            registry = RecognizerRegistry()
            # Don't use load_predefined_recognizers with languages param - it doesn't filter properly
            # Instead, we'll rely on our custom recognizers + the NLP-based ones
            registry.load_predefined_recognizers(nlp_engine=nlp_engine)
            
            # Add Canadian-specific recognizers (language-agnostic pattern-based)
            registry.add_recognizer(CanadianSINRecognizer())
            registry.add_recognizer(CanadianPostalCodeRecognizer())
            registry.add_recognizer(CanadianUCIRecognizer())
            registry.add_recognizer(CanadianPassportRecognizer())
            registry.add_recognizer(CanadianPhoneRecognizer())
            registry.add_recognizer(BankAccountRecognizer())
            
            # Get the actual supported languages from the registry
            registry_languages = registry.supported_languages
            logger.info(f"[OLI] Registry supports languages: {registry_languages}")
            
            # Use registry's languages to avoid mismatch
            self._analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                registry=registry,
                supported_languages=registry_languages
            )
            
            # Update our languages to match what's actually supported
            self.languages = list(registry_languages)
            self._available_languages = available_languages  # Languages with spaCy models
            
            self._anonymizer = AnonymizerEngine()
            
            logger.info(f"[OLI] Presidio initialized successfully with NER languages: {self._available_languages}")
            
        except Exception as e:
            logger.error(f"[OLI] Failed to initialize Presidio: {e}")
            self._use_presidio = False
    
    def _build_operator_configs(self) -> Dict[str, OperatorConfig]:
        """Build Presidio operator configs from replacement tokens"""
        return {
            entity_type: OperatorConfig("replace", {"new_value": replacement})
            for entity_type, replacement in self.operators.items()
        }
    
    def anonymize(self, text: str, language: str = None) -> str:
        """
        Anonymize text by replacing PII with tokens
        
        Args:
            text: Text to anonymize
            language: Language code (auto-detected if None)
        
        Returns:
            Anonymized text string
        """
        result = self.anonymize_with_details(text, language)
        return result.anonymized_text
    
    def anonymize_with_details(
        self, 
        text: str, 
        language: str = None
    ) -> AnonymizationResult:
        """
        Anonymize text and return detailed results
        
        Args:
            text: Text to anonymize
            language: Language code (auto-detected if None)
        
        Returns:
            AnonymizationResult with all details
        """
        if not text:
            return AnonymizationResult(
                original_text="",
                anonymized_text="",
                success=True
            )
        
        # Auto-detect language if not specified
        if language is None:
            language = self._detect_language(text)
        
        if self._use_presidio and self._analyzer and self._anonymizer:
            return self._presidio_anonymize(text, language)
        else:
            return self._fallback_anonymize(text)
    
    def _presidio_anonymize(self, text: str, language: str) -> AnonymizationResult:
        """Anonymize using Presidio"""
        try:
            # IMPORTANT: For French text, ALWAYS use regex fallback
            # English NER causes too many false positives on French words
            # (e.g., "Téléphone" detected as PERSON, "Adresse" as LOCATION)
            if language == "fr" or language not in self._available_languages:
                logger.info(f"[OLI] Using regex fallback for language: {language}")
                return self._fallback_anonymize(text)
            
            # For English text, use NER but only for specific entities
            # Analyze text for PII
            results = self._analyzer.analyze(
                text=text,
                language=language,
                score_threshold=self.score_threshold
            )
            
            # ONLY keep pattern-based entities (Canadian PII + standard patterns)
            # Skip generic NER entities (PERSON, LOCATION, ORGANIZATION) to avoid false positives
            pattern_based_entities = {
                'CA_SIN', 'CA_UCI', 'CA_POSTAL_CODE', 'CA_PASSPORT', 
                'EMAIL_ADDRESS', 'PHONE_NUMBER', 'CREDIT_CARD', 'IBAN_CODE',
                'IP_ADDRESS', 'URL', 'DATE_TIME'
            }
            
            filtered_results = [r for r in results if r.entity_type in pattern_based_entities]
            
            # Build entity list
            entities_detected = [
                DetectedEntity(
                    entity_type=r.entity_type,
                    text=text[r.start:r.end],
                    start=r.start,
                    end=r.end,
                    score=r.score
                )
                for r in filtered_results
            ]
            
            # Count by type
            entities_by_type = {}
            for entity in entities_detected:
                entities_by_type[entity.entity_type] = entities_by_type.get(entity.entity_type, 0) + 1
            
            # Anonymize
            operator_configs = self._build_operator_configs()
            anonymized = self._anonymizer.anonymize(
                text=text,
                analyzer_results=filtered_results,
                operators=operator_configs
            )
            
            return AnonymizationResult(
                original_text=text,
                anonymized_text=anonymized.text,
                entities_detected=entities_detected,
                entities_by_type=entities_by_type,
                success=True
            )
            
        except Exception as e:
            logger.error(f"[OLI] Presidio anonymization failed: {e}")
            # Fall back to regex
            return self._fallback_anonymize(text)
    
    def _fallback_anonymize(self, text: str) -> AnonymizationResult:
        """
        Fallback regex-based anonymization when Presidio is unavailable
        """
        anonymized = text
        entities_detected = []
        entities_by_type = {}
        
        # Define patterns and their entity types
        # Order matters: more specific patterns should come first
        patterns = [
            # Canadian SIN (must be before generic numbers)
            (r"\b\d{3}[-\s]\d{3}[-\s]\d{3}\b", "CA_SIN", "<SIN>"),
            # UCI
            (r"\bUCI[-\s]?\d{8,10}\b", "CA_UCI", "<UCI>"),
            # Canadian postal code
            (r"\b[A-Za-z]\d[A-Za-z][-\s]?\d[A-Za-z]\d\b", "CA_POSTAL_CODE", "<POSTAL_CODE>"),
            # Email (before phone to avoid conflicts)
            (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "EMAIL_ADDRESS", "<EMAIL>"),
            # Phone - Canadian format with country code (full match)
            (r"\+1[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b", "PHONE_NUMBER", "<PHONE>"),
            # Phone - standard format without country code
            (r"\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b", "PHONE_NUMBER", "<PHONE>"),
            # Credit card
            (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", "<CREDIT_CARD>"),
            # Canadian Passport (2 letters + 6 digits)
            (r"\b[A-Z]{2}\d{6}\b", "CA_PASSPORT", "<PASSPORT>"),
        ]
        
        # First pass: detect and replace standard patterns
        for pattern, entity_type, replacement in patterns:
            matches = list(re.finditer(pattern, anonymized, re.IGNORECASE if entity_type != "CA_PASSPORT" else 0))
            for match in matches:
                detected_text = match.group(0)
                entities_detected.append(DetectedEntity(
                    entity_type=entity_type,
                    text=detected_text,
                    start=match.start(),
                    end=match.end(),
                    score=0.8
                ))
                entities_by_type[entity_type] = entities_by_type.get(entity_type, 0) + 1
            
            flags = re.IGNORECASE if entity_type != "CA_PASSPORT" else 0
            anonymized = re.sub(pattern, replacement, anonymized, flags=flags)
        
        # Second pass: detect names after indicators (French/English)
        # Use [^\S\n] for spaces that are NOT newlines to avoid capturing across lines
        name_patterns = [
            # "Nom complet :" or "Nom :" followed by name (stops at newline)
            (r"(Nom\s+complet\s*:\s*)([A-Z][a-zéèêëàâäùûüôöîïç]+(?:[^\S\n]+[A-Z][a-zéèêëàâäùûüôöîïç]+)*)", r"\1<PERSON>"),
            (r"(Nom\s*:\s*)([A-Z][a-zéèêëàâäùûüôöîïç]+(?:[^\S\n]+[A-Z][a-zéèêëàâäùûüôöîïç]+)*)", r"\1<PERSON>"),
            # "Demandeur :" followed by name
            (r"(Demandeur\s*:\s*)([A-Z][a-zéèêëàâäùûüôöîïç]+(?:[^\S\n]+[A-Z][a-zéèêëàâäùûüôöîïç]+)*)", r"\1<PERSON>"),
            # "Name:" or "Applicant:" or "Full Name:" followed by name
            (r"(Full\s+Name\s*:\s*)([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+)*)", r"\1<PERSON>"),
            (r"(Name\s*:\s*)([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+)*)", r"\1<PERSON>"),
            (r"(Applicant\s*:\s*)([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+)*)", r"\1<PERSON>"),
        ]
        
        for pattern, replacement in name_patterns:
            matches = list(re.finditer(pattern, anonymized))
            for match in matches:
                if match.lastindex and match.lastindex >= 2:
                    detected_text = match.group(2)
                    entities_detected.append(DetectedEntity(
                        entity_type="PERSON",
                        text=detected_text,
                        start=match.start(2),
                        end=match.end(2),
                        score=0.8
                    ))
                    entities_by_type["PERSON"] = entities_by_type.get("PERSON", 0) + 1
            
            anonymized = re.sub(pattern, replacement, anonymized)
        
        return AnonymizationResult(
            original_text=text,
            anonymized_text=anonymized,
            entities_detected=entities_detected,
            entities_by_type=entities_by_type,
            success=True
        )
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words
        Returns 'fr' for French, 'en' for English
        """
        # Common French words and patterns
        french_indicators = [
            # Articles and prepositions
            "le", "la", "les", "de", "du", "des", "un", "une", "au", "aux",
            "ce", "cette", "ces", "mon", "ma", "mes", "son", "sa", "ses",
            # Verbs
            "est", "sont", "être", "avoir", "fait", "peut", "doit", "veut",
            "habite", "travaille", "comme",
            # Common words
            "et", "ou", "mais", "donc", "car", "que", "qui", "dans", "pour",
            "sur", "avec", "sans", "chez", "entre", "vers", "par",
            # Domain-specific (immigration/admin)
            "nom", "prénom", "adresse", "numéro", "demandeur", "dossier",
            "montant", "solde", "relevé", "bancaire", "courriel", "téléphone",
            "canadienne", "canadien", "citoyenne", "citoyen", "ingénieur",
            # Accented words (strong French indicator)
            "à", "où", "né", "née", "émission"
        ]
        
        # Common English words
        english_indicators = [
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "can", "could", "should", "may", "might", "must",
            "and", "or", "but", "if", "then", "because", "when", "where",
            "what", "which", "who", "how", "this", "that", "these", "those",
            "in", "on", "at", "to", "for", "with", "from", "by", "about"
        ]
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        word_set = set(words)
        
        # Count matches
        french_count = sum(1 for word in french_indicators if word in word_set)
        english_count = sum(1 for word in english_indicators if word in word_set)
        
        # Check for French accented characters (strong indicator)
        french_accents = len(re.findall(r'[éèêëàâäùûüôöîïç]', text_lower))
        french_count += french_accents * 2  # Weight accents more heavily
        
        # If clearly French (more French indicators or accents)
        if french_count > english_count or french_accents >= 2:
            return "fr"
        
        return "en"
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        if self._use_presidio and self._analyzer:
            return self._analyzer.get_supported_entities()
        return list(self.operators.keys())
    
    def detect_entities(self, text: str, language: str = None) -> List[DetectedEntity]:
        """
        Detect PII entities without anonymizing
        
        Args:
            text: Text to analyze
            language: Language code
        
        Returns:
            List of detected entities
        """
        result = self.anonymize_with_details(text, language)
        return result.entities_detected
    
    def is_available(self) -> bool:
        """Check if Presidio is properly initialized"""
        return self._use_presidio and self._analyzer is not None


# Singleton instance
_anonymizer_instance: Optional[PresidioAnonymizer] = None


def get_anonymizer(
    languages: List[str] = None,
    force_new: bool = False
) -> PresidioAnonymizer:
    """
    Get or create the global anonymizer instance
    
    Args:
        languages: Languages to support
        force_new: Force creation of new instance
    
    Returns:
        PresidioAnonymizer instance
    """
    global _anonymizer_instance
    
    if _anonymizer_instance is None or force_new:
        _anonymizer_instance = PresidioAnonymizer(languages=languages)
    
    return _anonymizer_instance


# CLI test
if __name__ == "__main__":
    print("=" * 60)
    print("OLI Presidio Anonymizer Test")
    print("=" * 60)
    
    anonymizer = get_anonymizer()
    
    # Test text with Canadian PII
    test_text = """
    Demandeur : Sophie Martin
    Numéro UCI : UCI-12345678
    NAS : 123-456-789
    Courriel : sophie.martin@email.com
    Téléphone : +1 (514) 555-1234
    Code postal : H2X 1Y4
    Solde moyen : 5 000 $
    Date du relevé : 2024-01-15
    """
    
    print("\n[Original Text]")
    print(test_text)
    
    print("\n[Anonymized Text]")
    result = anonymizer.anonymize_with_details(test_text)
    print(result.anonymized_text)
    
    print("\n[Detected Entities]")
    for entity in result.entities_detected:
        print(f"  - {entity.entity_type}: '{entity.text}' (score: {entity.score:.2f})")
    
    print("\n[Summary]")
    print(f"  Total entities: {len(result.entities_detected)}")
    print(f"  By type: {result.entities_by_type}")
    print(f"  Presidio available: {anonymizer.is_available()}")

