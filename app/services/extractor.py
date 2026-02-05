"""
Intelligence Extraction Service
"""

import re
import logging
from typing import List, Dict, Any

from app.models import Intelligence
from app.prompts import EXTRACTION_PROMPT
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """Service for extracting scam intelligence from conversations"""
    
    # Regex patterns for extraction
    PATTERNS = {
        # UPI ID: username@bankname or number@upi
        "upi": re.compile(
            r'\b([a-zA-Z0-9._-]+@[a-zA-Z]+)\b',
            re.IGNORECASE
        ),
        # Bank account: 9-18 digits
        "bank_account": re.compile(
            r'\b(\d{9,18})\b'
        ),
        # IFSC: 4 letters + 7 alphanumeric
        "ifsc": re.compile(
            r'\b([A-Z]{4}0[A-Z0-9]{6})\b',
            re.IGNORECASE
        ),
        # URL patterns
        "url": re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        ),
        # Phone: Indian format with optional country code
        "phone": re.compile(
            r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b|\b(?:\+91[-\s]?)?\d{5}[-\s]?\d{5}\b'
        ),
    }
    
    # UPI bank suffixes
    UPI_SUFFIXES = [
        '@ybl', '@upi', '@paytm', '@oksbi', '@okicici', '@okhdfcbank',
        '@axl', '@ibl', '@sbi', '@icici', '@hdfc', '@axis', '@kotak',
        '@freecharge', '@apl', '@pnb', '@boi', '@cbin', '@federal'
    ]
    
    def __init__(self):
        self._llm = get_llm_service()
    
    def _regex_extraction(self, text: str) -> Intelligence:
        """
        Extract intelligence using regex patterns
        
        Args:
            text: Text to extract from
            
        Returns:
            Intelligence object with extracted data
        """
        # Extract UPI IDs
        upi_matches = self.PATTERNS["upi"].findall(text)
        upi_ids = [
            match for match in upi_matches
            if any(match.lower().endswith(suffix) for suffix in self.UPI_SUFFIXES)
        ]
        
        # Extract bank accounts
        bank_accounts = list(set(self.PATTERNS["bank_account"].findall(text)))
        
        # Extract IFSC codes
        ifsc_codes = list(set(self.PATTERNS["ifsc"].findall(text.upper())))
        
        # Extract URLs
        urls = list(set(self.PATTERNS["url"].findall(text)))
        
        # Extract phone numbers and normalize
        phone_matches = self.PATTERNS["phone"].findall(text)
        phones = []
        for phone in phone_matches:
            # Normalize: remove spaces and hyphens
            normalized = re.sub(r'[-\s]', '', phone)
            if normalized not in phones:
                phones.append(normalized)
        
        return Intelligence(
            upi_ids=list(set(upi_ids)),
            bank_accounts=bank_accounts,
            ifsc_codes=ifsc_codes,
            urls=urls,
            phones=phones
        )
    
    async def extract(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Intelligence:
        """
        Extract intelligence from full conversation history
        
        Uses LLM extraction with regex fallback
        
        Args:
            conversation_history: List of conversation turns
            
        Returns:
            Intelligence object with extracted data
        """
        # Combine all messages into text
        full_text = "\n".join([
            turn.get("content", "") for turn in conversation_history
        ])
        
        # First, apply regex extraction
        regex_intel = self._regex_extraction(full_text)
        
        try:
            # Build conversation text for LLM
            conversation_text = ""
            for turn in conversation_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                conversation_text += f"{role}: {content}\n"
            
            # Get LLM extraction
            result = await self._llm.complete_json(
                system_prompt=EXTRACTION_PROMPT,
                user_message=f"Extract intelligence from this conversation:\n\n{conversation_text}",
                temperature=0.1
            )
            
            # Merge LLM and regex results
            llm_intel = Intelligence(
                upi_ids=result.get("upi_ids", []),
                bank_accounts=result.get("bank_accounts", []),
                ifsc_codes=result.get("ifsc_codes", []),
                urls=result.get("urls", []),
                phones=result.get("phones", [])
            )
            
            # Combine unique values
            combined = Intelligence(
                upi_ids=list(set(regex_intel.upi_ids + llm_intel.upi_ids)),
                bank_accounts=list(set(regex_intel.bank_accounts + llm_intel.bank_accounts)),
                ifsc_codes=list(set(regex_intel.ifsc_codes + llm_intel.ifsc_codes)),
                urls=list(set(regex_intel.urls + llm_intel.urls)),
                phones=list(set(regex_intel.phones + llm_intel.phones))
            )
            
            logger.info(
                f"Extracted intelligence: "
                f"upi={len(combined.upi_ids)}, "
                f"accounts={len(combined.bank_accounts)}, "
                f"urls={len(combined.urls)}, "
                f"phones={len(combined.phones)}"
            )
            
            return combined
            
        except Exception as e:
            logger.warning(f"LLM extraction failed, using regex only: {e}")
            return regex_intel


# Singleton instance
_extractor_service = None


def get_extractor_service() -> IntelligenceExtractor:
    """Get or create extractor service singleton"""
    global _extractor_service
    if _extractor_service is None:
        _extractor_service = IntelligenceExtractor()
    return _extractor_service
