import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import Presidio - requires C++ build tools to install
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.warning("[PIIRedactor] Presidio not available. PII redaction disabled.")

class PIIRedactor:
    def __init__(self, entities: Optional[List[str]] = None):
        """
        Initialize the PII Redactor using Microsoft Presidio.
        
        :param entities: List of entities to redact. If None, uses a standard set.
        """
        self._enabled = PRESIDIO_AVAILABLE
        
        if not self._enabled:
            return
            
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Default entities if none provided
        self.entities = entities or [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", 
            "LOCATION", "DATE_TIME", "CRYPTO", 
            "IBAN_CODE", "MEDICAL_LICENSE", "US_BANK_NUMBER", 
            "US_DRIVER_LICENSE", "US_ITIN", "US_PASSPORT", 
            "US_SSN"
        ]
        
        # Configure operators for each entity. Default is to replace with entity name.
        self.operators = {
            entity: OperatorConfig("replace", {"new_value": f"<{entity}>"}) 
            for entity in self.entities
        }

    def redact(self, text: str) -> Tuple[str, int]:
        """
        Analyzes and redacts PII from the given text.
        Returns a tuple of (redacted_text, count_of_redactions).
        """
        # If Presidio not available, return text unchanged
        if not self._enabled:
            return text, 0
            
        if not text or not isinstance(text, str):
            return text, 0
            
        try:
            # 1. Analyze text for PII
            analysis_results = self.analyzer.analyze(
                text=text, 
                entities=self.entities, 
                language='en'
            )
            
            count = len(analysis_results)
            if count == 0:
                return text, 0

            # 2. Anonymize/Redact detected entities
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analysis_results,
                operators=self.operators
            )
            
            return anonymized_result.text, count
            
        except Exception as e:
            logger.error(f"Error during PII redaction: {e}")
            return text, 0

# Singleton instance for easy access
redactor = PIIRedactor()

