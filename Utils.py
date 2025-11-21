import logging
import re
from typing import Dict, List

from dtos.Challenge import Challenge

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Utils:
    def clean_json(raw_content: str) -> str:
        """Clean JSON from various markdown formats"""
        content = raw_content.strip()
        
        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
        
        content = content.strip()
        
        if not content.startswith('['):
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                content = match.group(0)
        
        return content

    def validate_challenges(challenges: List[Dict]) -> List[Challenge]:
        """Validate and parse challenges"""
        validated = []
        for idx, challenge in enumerate(challenges):
            try:
                validated.append(Challenge(**challenge))
            except Exception as e:
                logger.warning(f"Challenge {idx} validation failed: {e}")
                continue
        return validated