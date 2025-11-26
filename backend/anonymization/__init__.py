"""
OLI Anonymization Module
Microsoft Presidio-based PII anonymization for Canadian data
"""

from .presidio_anonymizer import (
    PresidioAnonymizer,
    get_anonymizer,
    AnonymizationResult
)

__all__ = [
    "PresidioAnonymizer",
    "get_anonymizer", 
    "AnonymizationResult"
]

