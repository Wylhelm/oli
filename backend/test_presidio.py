"""
OLI Presidio Anonymization Test Suite

Tests Microsoft Presidio integration with Canadian-specific recognizers:
- CA_SIN: Canadian Social Insurance Number
- CA_UCI: Immigration Unique Client Identifier
- CA_POSTAL_CODE: Canadian Postal Codes
- CA_PASSPORT: Canadian Passport Numbers
- Plus standard PII: Names, Emails, Phones, Credit Cards, etc.

Usage:
    cd backend
    python test_presidio.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from anonymization.presidio_anonymizer import (
    PresidioAnonymizer,
    get_anonymizer,
    AnonymizationResult
)


def print_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(label: str, value: str, indent: int = 0):
    """Print a labeled result"""
    prefix = "  " * indent
    print(f"{prefix}{label}: {value}")


def test_canadian_pii():
    """Test Canadian-specific PII detection"""
    print_header("Test 1: Canadian PII Detection")
    
    test_cases = [
        {
            "name": "SIN (with dashes)",
            "text": "Mon NAS est 123-456-789",
            "expected_entity": "CA_SIN"
        },
        {
            "name": "SIN (with spaces)",
            "text": "Social Insurance Number: 987 654 321",
            "expected_entity": "CA_SIN"
        },
        {
            "name": "UCI (IRCC)",
            "text": "Client identifier: UCI-12345678",
            "expected_entity": "CA_UCI"
        },
        {
            "name": "Postal Code",
            "text": "Adresse: 123 rue Main, Montréal, H2X 1Y4",
            "expected_entity": "CA_POSTAL_CODE"
        },
        {
            "name": "Passport",
            "text": "Passport number: AB123456",
            "expected_entity": "CA_PASSPORT"
        }
    ]
    
    anonymizer = get_anonymizer()
    
    for case in test_cases:
        print(f"\n[{case['name']}]")
        print(f"  Input:    {case['text']}")
        
        result = anonymizer.anonymize_with_details(case['text'])
        print(f"  Output:   {result.anonymized_text}")
        
        if result.entities_detected:
            entities_found = [e.entity_type for e in result.entities_detected]
            print(f"  Entities: {entities_found}")
            
            if case['expected_entity'] in entities_found:
                print(f"  ✅ PASS: Found {case['expected_entity']}")
            else:
                print(f"  ⚠️  WARN: Expected {case['expected_entity']}, found {entities_found}")
        else:
            print(f"  ⚠️  No entities detected (Presidio may be in fallback mode)")


def test_standard_pii():
    """Test standard PII detection"""
    print_header("Test 2: Standard PII Detection")
    
    test_cases = [
        {
            "name": "Email",
            "text": "Contact: sophie.martin@email.com",
            "expected_token": "<COURRIEL>"
        },
        {
            "name": "Phone (Canadian format)",
            "text": "Téléphone: +1 (514) 555-1234",
            "expected_token": "<TELEPHONE>"
        },
        {
            "name": "Credit Card",
            "text": "Card: 4111-1111-1111-1111",
            "expected_token": "<CARTE_CREDIT>"
        }
    ]
    
    anonymizer = get_anonymizer()
    
    for case in test_cases:
        print(f"\n[{case['name']}]")
        print(f"  Input:    {case['text']}")
        
        result = anonymizer.anonymize(case['text'])
        print(f"  Output:   {result}")
        
        if case['expected_token'] in result:
            print(f"  ✅ PASS: Token {case['expected_token']} found")
        else:
            print(f"  ⚠️  WARN: Token {case['expected_token']} not found")


def test_immigration_document():
    """Test with realistic immigration document"""
    print_header("Test 3: Full Immigration Document")
    
    document = """
    ===== DOSSIER D'IMMIGRATION =====
    
    INFORMATIONS DU DEMANDEUR
    -------------------------
    Nom complet : Sophie Martin
    Numéro UCI : UCI-12345678
    Numéro d'assurance sociale : 123-456-789
    Date de naissance : 1985-03-15
    
    COORDONNÉES
    -----------
    Courriel : sophie.martin@gmail.com
    Téléphone : +1 (514) 555-1234
    Adresse : 456 rue Sainte-Catherine, Montréal, QC H2X 1Y4
    
    INFORMATIONS FINANCIÈRES
    ------------------------
    Type de preuve : Relevé bancaire certifié
    Institution : Banque Nationale
    Compte : 12345-67890
    Solde moyen (6 derniers mois) : 25 000 $
    Date du relevé : 2024-10-15
    
    DOCUMENTS D'IDENTITÉ
    --------------------
    Passeport : AB123456
    Pays d'émission : Canada
    Date d'expiration : 2028-06-30
    """
    
    anonymizer = get_anonymizer()
    result = anonymizer.anonymize_with_details(document)
    
    print("\n[Original Document]")
    print(document)
    
    print("\n[Anonymized Document]")
    print(result.anonymized_text)
    
    print("\n[Detected Entities]")
    if result.entities_detected:
        for entity in result.entities_detected:
            print(f"  - {entity.entity_type}: '{entity.text}' (score: {entity.score:.2f})")
    else:
        print("  (No entities detected with Presidio - using fallback)")
    
    print("\n[Summary]")
    print(f"  Total entities found: {len(result.entities_detected)}")
    print(f"  Entities by type: {result.entities_by_type}")


def test_language_detection():
    """Test automatic language detection"""
    print_header("Test 4: Language Detection")
    
    test_cases = [
        {
            "name": "French text",
            "text": "Le demandeur habite à Montréal et travaille comme ingénieur.",
            "expected_lang": "fr"
        },
        {
            "name": "English text",
            "text": "The applicant lives in Toronto and works as an engineer.",
            "expected_lang": "en"
        },
        {
            "name": "Mixed (French dominant)",
            "text": "Sophie Martin est une citoyenne canadienne. She lives in Montreal.",
            "expected_lang": "fr"
        }
    ]
    
    anonymizer = get_anonymizer()
    
    for case in test_cases:
        print(f"\n[{case['name']}]")
        print(f"  Text: {case['text']}")
        detected = anonymizer._detect_language(case['text'])
        print(f"  Detected: {detected}")
        print(f"  Expected: {case['expected_lang']}")
        
        if detected == case['expected_lang']:
            print(f"  ✅ PASS")
        else:
            print(f"  ⚠️  Different from expected")


def test_preserves_amounts():
    """Test that financial amounts are NOT anonymized"""
    print_header("Test 5: Financial Amount Preservation")
    
    test_cases = [
        "Le solde est de 25 000 $",
        "Balance: $50,000 CAD",
        "Montant requis: 20 635 $",
        "Income: 75000$/year"
    ]
    
    anonymizer = get_anonymizer()
    
    for text in test_cases:
        result = anonymizer.anonymize(text)
        print(f"\n  Input:  {text}")
        print(f"  Output: {result}")
        
        # Check if dollar amounts are preserved
        import re
        original_amounts = re.findall(r'\d[\d\s,]*\s?\$|\$\s?\d[\d\s,]*', text)
        preserved = all(amt.replace(" ", "") in result.replace(" ", "") for amt in original_amounts)
        
        if preserved or not original_amounts:
            print(f"  ✅ Amounts preserved")
        else:
            print(f"  ⚠️  Some amounts may have been modified")


def test_presidio_status():
    """Test Presidio availability status"""
    print_header("Test 6: Presidio Status Check")
    
    # Force new instance to pick up any changes
    anonymizer = get_anonymizer(force_new=True)
    
    print(f"\n  Presidio Available: {anonymizer.is_available()}")
    print(f"  Supported Languages: {anonymizer.languages}")
    print(f"  Supported Entities: {len(anonymizer.get_supported_entities())} types")
    
    if anonymizer.is_available():
        print("\n  ✅ Presidio is running with full NER support")
    else:
        print("\n  ⚠️  Presidio is running in regex fallback mode")
        print("     To enable full NER, install spaCy models:")
        print("       python -m spacy download en_core_web_sm")
        print("       python -m spacy download fr_core_news_sm")


def run_all_tests():
    """Run all tests"""
    print("\n" + "🛡️ " * 20)
    print("\n   OLI PRESIDIO ANONYMIZATION TEST SUITE")
    print("\n" + "🛡️ " * 20)
    
    test_presidio_status()
    test_canadian_pii()
    test_standard_pii()
    test_immigration_document()
    test_language_detection()
    test_preserves_amounts()
    
    print_header("TEST SUITE COMPLETED")
    print("\n  Check results above for any warnings or failures.")
    print("  For full Presidio NER support, ensure spaCy models are installed.\n")


if __name__ == "__main__":
    run_all_tests()

