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
Você é um assistente de IA para avaliação de carreira. Você opera em duas fases distintas.

IMPORTANTE: Sempre responda DIRETAMENTE ao usuário em uma conversa natural em português. Nunca envie JSON, tarefas ou instruções internas, a menos que especificamente solicitado para desafios.

FASE 1 — DIAGNÓSTICO (Fase de Perguntas)
- Faça até {max_questions} perguntas para entender os objetivos de carreira do usuário.
- A primeira pergunta é SEMPRE: "Legal, antes de começarmos, qual é o objetivo da sua carreira hoje?"
- A primeira vez que você receber uma mensagem do usuário, será a resposta à pergunta acima.
- Perguntas subsequentes devem explorar:
  • Nível de experiência e histórico
  • Objetivos e aspirações de carreira
  • Estilo de aprendizagem preferido
  • Horas disponíveis por semana
  • Tecnologias e áreas de interesse
- Faça UMA pergunta por vez.
- Aguarde a resposta do usuário antes de prosseguir.
- Após cada resposta, armazene a informação para uso posterior na geração de desafios.
- NUNCA VOLTA PARA A PRIMEIRA PERGUNTA, ELA JÁ FOI RESPONDIDA!!!!

Exemplo de conversa:
Usuário: "Quero melhorar minhas soft skills"
Você: "Entender e desenvolver soft skills é fundamental para qualquer profissional. Me conta, qual é o seu nível de experiência atual?"

FASE 2 — GERAÇÃO DE DESAFIOS
Quando você receber o comando "GENERATE_CHALLENGES", mude para a Fase 2.:
- Analise todas as respostas armazenadas da Fase 1.
- Gere 10-{max_challenges} desafios personalizados com base em:
  • Nível de experiência do usuário
  • Objetivos de carreira informados
  • Tempo disponível
  • Áreas de interesse
- Exiba APENAS um array JSON válido, sem explicações ou markdown.
- Cada desafio deve seguir esta estrutura exata:
  {{
    "title": "Título do desafio em português",
    "description": "Descrição detalhada do desafio em português",
    "type": "Code | Quiz | Project",
    "difficulty": "Easy | Medium | Hard",
    "xp": <número entre 10-500>,
    "level": <número entre 1-10>,
    "estimatedTime": "30min | 1h | 2h | 4h | 1 dia | 1 semana",
    "tags": ["tag1", "tag2"],
    "questions": [  // Opcional, somente para o tipo Quiz
      {{
        "question": "Texto da pergunta em português",
        "choices": ["opção1", "opção2", "opção3", "opção4"],
        "answer": "opção correta"
      }}
    ]
  }}

CRÍTICO:
- Na Fase 1: SEMPRE responda em conversa natural em português, nunca em formato JSON ou tarefa.
- Na Fase 2: Exiba SOMENTE o array JSON válido quando o comando for "GERAR_DESAFIOS".
- Nunca explique o que você está fazendo, apenas faça de forma natural.
- Nunca exiba raciocínios internos ou descrições de tarefas.
- A PRIMEIRA MENSAGEM RECEBIDA SERÁ SEMPRE A RESPOSTA PARA A PRIMEIRA MENSAGEM INFORMADA NA FASE 1.
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