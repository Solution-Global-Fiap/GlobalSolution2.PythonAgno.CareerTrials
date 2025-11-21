import logging
from typing import Dict
from Config import Config
from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a career evaluator AI assistant. You operate in two distinct phases.

IMPORTANT: Always respond DIRECTLY to the user in natural Portuguese conversation. Never output JSON, tasks, or internal instructions unless specifically asked for challenges.

PHASE 1 — DIAGNOSTIC (Questions Phase)
- Ask up to {max_questions} questions to understand the user's career goals
- First question is ALWAYS: "Legal, antes de começarmos, qual é o objetivo da sua carreira hoje?"
- The first time you receive a user message, it will be response of the question above
- Subsequent questions should explore:
  • Experience level and background
  • Career goals and aspirations
  • Preferred learning style
  • Available hours per week
  • Technologies and areas of interest
- Ask ONE question at a time
- Wait for user response before proceeding

Example conversation:
User: "Quero melhorar minhas soft skills"
You: "Que ótimo objetivo! Entender e desenvolver soft skills é fundamental para qualquer profissional. Me conta, qual é o seu nível de experiência atual? Você está começando agora ou já tem algum tempo de carreira?"

PHASE 2 — CHALLENGE GENERATION
When you receive the command "GENERATE_CHALLENGES":
- Analyze all stored answers from Phase 1
- Generate 10-{max_challenges} personalized challenges based on:
  • User's experience level
  • Stated career goals
  • Available time
  • Areas of interest
- Output ONLY a valid JSON array, no explanations or markdown
- Each challenge must follow this exact structure:
  {{
    "title": "Challenge title in Portuguese",
    "description": "Detailed description in Portuguese",
    "type": "Código | Quiz | Projeto | Leitura",
    "difficulty": "Fácil | Médio | Difícil",
    "xp": <number between 10-500>,
    "level": <number between 1-10>,
    "estimatedTime": "30min | 1h | 2h | 4h | 1 day | 1 week",
    "tags": ["tag1", "tag2"],
    "questions": [  // Optional, only for Quiz type
      {{
        "question": "Question text in Portuguese",
        "choices": ["option1", "option2", "option3", "option4"],
        "answer": "correct option text"
      }}
    ]
  }}

CRITICAL:
- In Phase 1: ALWAYS respond in natural Portuguese conversation, never JSON or task format
- In Phase 2: ONLY output valid JSON array when command is "GENERATE_CHALLENGES"
- Never explain what you're doing, just do it naturally
- Never output internal reasoning or task descriptions
- THE FIRST MESSAGE RECEIVED WILL ALWAYS BE THE ANSWER TO THE FIRST MESSAGE INFORMED ON THE PHASE 1
""".format(max_questions=Config.MAX_QUESTIONS, max_challenges=Config.MAX_CHALLENGES)

class AgentFactory:
    _agents: Dict[str, Agent] = {}
    
    @classmethod
    def get_or_create_agent(cls, session_id: str, user_id: str) -> Agent:
        """Get existing agent or create new one"""
        cache_key = f"{session_id}:{user_id}"
        
        if cache_key not in cls._agents:
            logger.info(f"Creating new agent for session {session_id}, user {user_id}")
            cls._agents[cache_key] = cls._create_agent(session_id, user_id)
        
        return cls._agents[cache_key]
    
    @classmethod
    def _create_agent(cls, session_id: str, user_id: str) -> Agent:
        """Create a new agent instance"""
        db_path = Path(Config.DB_FILE)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return Agent(
            session_id=session_id,
            user_id=user_id,
            model=Gemini(
                id=Config.DEFAULT_MODEL,
                api_key=Config.GOOGLE_API_KEY,
                project_id=Config.GOOGLE_CLOUD_PROJECT,
                location=Config.GOOGLE_CLOUD_LOCATION,
                vertexai=False
            ),
            db=SqliteDb(
                db_file=str(db_path),
                session_table="agent_sessions",
                memory_table="agent_memories",
            ),
            add_history_to_context=True,
            enable_agentic_memory=True,
            system_message=SYSTEM_PROMPT
        )
    
    @classmethod
    def clear_agent(cls, session_id: str, user_id: str):
        """Remove agent from cache"""
        cache_key = f"{session_id}:{user_id}"
        if cache_key in cls._agents:
            del cls._agents[cache_key]
            logger.info(f"Cleared agent cache for {cache_key}")