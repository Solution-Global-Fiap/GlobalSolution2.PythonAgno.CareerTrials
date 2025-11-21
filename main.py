import json

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from AgentFactory import AgentFactory
from Config import Config
from Utils import Utils
from dtos.ChallengesResponse import ChallengesResponse
from dtos.ErrorResponse import ErrorResponse
from dtos.MessageRequest import MessageRequest
from dtos.MessageResponse import MessageResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Config.validate()

app = FastAPI(
    title="CareerTrials AI API",
    description="AI-powered career guidance and challenge generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CareerTrials AI API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "model": Config.DEFAULT_MODEL
    }

@app.post("/session/{session_id}/{user_id}/message")
async def send_message(session_id: str, user_id: str, body: MessageRequest):
    """
    Send a message to the AI agent
    
    - **session_id**: Unique session identifier
    - **user_id**: User identifier
    - **message**: User's message
    """
    try:
        logger.info(f"Received message from user {user_id} in session {session_id}")
        
        agent = AgentFactory.get_or_create_agent(session_id, user_id)
        response = agent.run(body.message)

        cleaned_response = Utils.extract_user_response(response.content)
        
        # If we got internal response multiple times, retry with explicit instruction
        retry_count = 0
        while Utils.is_internal_response(cleaned_response) and retry_count < 2:
            logger.warning(f"Retry {retry_count + 1}: Got internal response, asking again")
            response = agent.run("Por favor, responda diretamente ao usuário em português, não em formato JSON ou tarefa.")
            cleaned_response = Utils.extract_user_response(response.content)
            retry_count += 1
        
        return MessageResponse(
            response=cleaned_response,
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@app.post("/session/{session_id}/{user_id}/complete", response_model=ChallengesResponse)
async def generate_challenges(session_id: str, user_id: str):
    """
    Generate personalized challenges based on conversation history
    
    - **session_id**: Unique session identifier
    - **user_id**: User identifier
    """
    try:
        logger.info(f"Generating challenges for user {user_id} in session {session_id}")
        
        agent = AgentFactory.get_or_create_agent(session_id, user_id)
        result = agent.run("GENERATE_CHALLENGES")
        
        # Clean and parse JSON
        raw_content = result.content.strip()
        cleaned_content = Utils.clean_json(raw_content)
        
        try:
            challenges_data = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}\nRaw content: {raw_content}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse(
                    error="Failed to parse challenges",
                    detail=str(e),
                    raw_output=raw_content
                ).model_dump()
            )
        
        if not isinstance(challenges_data, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Expected array of challenges"
            )
        
        validated_challenges = Utils.validate_challenges(challenges_data)
        
        if not validated_challenges:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No valid challenges generated"
            )
        
        logger.info(f"Successfully generated {len(validated_challenges)} challenges")
        
        return ChallengesResponse(
            challenges=validated_challenges,
            total=len(validated_challenges),
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating challenges: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate challenges: {str(e)}"
        )

@app.delete("/session/{session_id}/{user_id}")
async def delete_session(session_id: str, user_id: str):
    """
    Delete a session and clear agent cache
    
    - **session_id**: Unique session identifier
    - **user_id**: User identifier
    """
    try:
        AgentFactory.clear_agent(session_id, user_id)
        return {"message": "Session cleared successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )

@app.get("/session/{session_id}/{user_id}/status")
async def get_session_status(session_id: str, user_id: str):
    """
    Get session status and metadata
    
    - **session_id**: Unique session identifier
    - **user_id**: User identifier
    """
    cache_key = f"{session_id}:{user_id}"
    exists = cache_key in AgentFactory._agents
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "active": exists,
        "status": "active" if exists else "inactive"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)