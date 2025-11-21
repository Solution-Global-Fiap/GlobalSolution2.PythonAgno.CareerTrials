import json
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
    def is_internal_response(content: str) -> bool:
        """Check if response is internal reasoning instead of user-facing"""
        content_lower = content.lower().strip()
        
        # Check for JSON task format
        if content_lower.startswith('```json') or content_lower.startswith('{'):
            try:
                # Try to parse as JSON
                if content.startswith('```json'):
                    json_content = content[7:-3].strip() if content.endswith('```') else content[7:].strip()
                else:
                    json_content = content
                
                parsed = json.loads(json_content)
                # If it has 'task' key, it's internal reasoning
                if isinstance(parsed, dict) and 'task' in parsed:
                    return True
            except:
                pass
    
        # Check for internal task keywords
        internal_keywords = [
            'adicionar a seguinte informação',
            'task":',
            'armazenar na memória',
            'salvar informação',
            'registrar resposta'
        ]
        
        return any(keyword in content_lower for keyword in internal_keywords)

    def extract_user_response(agent_response: str) -> str:
        """Extract actual user-facing response, filtering out internal reasoning"""
        content = agent_response.strip()
        
        # If it's internal reasoning, return a fallback message
        if Utils.is_internal_response(content):
            logger.warning("Detected internal response, using fallback")
            return "Entendi! Qual é a sua próxima resposta?"
        
        return content

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