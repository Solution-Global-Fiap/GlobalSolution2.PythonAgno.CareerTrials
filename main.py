import json
import os
from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

def create_agent(session_id: str, user_id: str) -> Agent:
    return Agent(
        session_id=session_id,
        user_id=user_id,
        model=Gemini(
            id=os.getenv("DEFAULT_MODEL"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            vertexai=False
        ),
        db=SqliteDb(
            db_file="tmp/agents.db", 
            session_table="agent_sessions",
            memory_table="agent_memories",
        ),
        add_history_to_context=True,
        enable_agentic_memory=True,
        system_message="""
            You are a career evaluator. You operate in two phases.

            Only ask up to FIVE questions to the user

            PHASE 1 — DIAGNOSTIC
            Ask the user up to 5 questions to understand:
            - The first questions will always be "Legal, antes de começarmos, qual é o objetivo da sua carreira hoje?"
            - The first message received will be the answer to that question.
            - experience level
            - goals
            - preferred learning style
            - available hours
            - technologies of interest

            Store each answer in memory as:
            memory.answers.append({question, answer})

            Only ask ONE question at a time.

            PHASE 2 — CHALLENGE GENERATION
            When instructed "GENERATE_CHALLENGES":
            - Analyze memory.answers
            - Produce a JSON array with up to 20 personalized challenges
            - No explanations, only JSON
            - Respond only with a JSON array of 1-20 challenges.
            - Each challenge must contain:
                {
                    "title": "...",
                    "description": "...",
                    "type": "Código | Quiz | Projeto | Leitura",
                    "difficulty": "Fácil | Médio | Difícil",
                    "xp": number,
                    "level": number,
                    "questions": [
                        "question": "...",
                        "choices": ["...", "...", "...", "..."],
                        "answer": "..."
                    ] optional
                }
            - The `title`, `description` and `questions` must be in portuguese Brazil.
            - Your response must NOT include explanations.
            - Only valid JSON.
        """
    )

class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    
    @field_validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class MessageResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    is_complete: bool = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Body(BaseModel):
    message: str

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "CareerTrials AI API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "connected",
        "model": os.getenv("DEFAULT_MODEL")
    }

@app.post("/session/{session_id}/{user_id}/message", response_model=MessageResponse)
async def handle_message(session_id: str, user_id: str, body: MessageRequest):
    """
    Send a message to the AI agent
    
    - **session_id**: Unique session identifier
    - **user_id**: User identifier
    - **message**: User's message
    """
    try:
        agent = create_agent(session_id, user_id)
        response = agent.run(body.message)

        return MessageResponse(
            response=response.content,
            session_id=session_id,
            user_id=user_id,
            is_complete=("GENERATE_CHALLENGES" in body.message)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@app.post("/session/{session_id}/{user_id}/complete")
async def complete(session_id: str, user_id: str):
    agent = create_agent(session_id, user_id)

    result = agent.run("GENERATE_CHALLENGES")

    raw_content = result.content.strip()

    cleaned_content = ""

    if raw_content.startswith("```json") and raw_content.endswith("```"):
        cleaned_content = raw_content[7:-3].strip()
    else:
        cleaned_content = raw_content

    challenges_data = []

    try:
        challenges_data = json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
        return {"error": "Falha ao processar o conteúdo do Agno.", "raw_output": raw_content}

    return {"challenges": challenges_data}