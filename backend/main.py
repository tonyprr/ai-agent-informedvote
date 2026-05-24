import uvicorn
import logging
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

from .rag import init_pinecone_index, ingest_local_data
from .agent import rag_graph
from .utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Pinecone Index on startup
    logger.info("Initializing Pinecone Index...")
    try:
        init_pinecone_index()
        logger.info("Pinecone Index initialization complete.")
    except Exception as e:
        logger.exception("Failed to initialize Pinecone Index on startup:")
    yield

fastapi_app = FastAPI(title="MultiPDF RAG Engine (LangGraph)", lifespan=lifespan)

class QueryRequest(BaseModel):
    prompt: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    duration: float
    input_tokens: int
    output_tokens: int
    total_tokens: int

@fastapi_app.post("/ingest")
def trigger_ingestion():
    logger.info("Triggering PDF ingestion from local directory...")
    try:
        result = ingest_local_data()
        logger.info(f"Ingestion finished: {result}")
        return result
    except Exception as e:
        logger.exception("Error during PDF ingestion:")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    logger.info(f"Received query request for session '{request.session_id}': '{request.prompt}'")
    try:
        # Start timer
        start_time = time.time()
        
        # Checkpointer thread configuration for automatic LangGraph memory
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Invoke LangGraph agent
        logger.info("Invoking LangGraph agent...")
        inputs = {"messages": [("user", request.prompt)]}
        res = rag_graph.invoke(inputs, config=config)
        logger.info("Agent execution completed successfully.")
        
        # Calculate processing duration
        duration = time.time() - start_time
        
        all_messages = res.get("messages", [])
        
        # Extract sources by finding ToolMessages with artifacts in this turn
        sources = []
        last_human_idx = -1
        for i in range(len(all_messages)-1, -1, -1):
            if all_messages[i].type == "human":
                last_human_idx = i
                break
                
        # Parse tokens only for the current turn (messages after the last human message)
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        
        for msg in all_messages[last_human_idx+1:]:
            # Extract metadata and sources
            if msg.type == "tool" and hasattr(msg, "artifact") and msg.artifact:
                if isinstance(msg.artifact, dict) and "sources" in msg.artifact:
                    sources.extend(msg.artifact["sources"])
            
            # Extract token usage from LLM response messages
            if msg.type == "ai" and hasattr(msg, "usage_metadata") and msg.usage_metadata:
                usage = msg.usage_metadata
                input_tokens += usage.get("input_tokens", 0)
                output_tokens += usage.get("output_tokens", 0)
                total_tokens += usage.get("total_tokens", 0)
                    
        sources = list(set(sources))
        
        # Extract text content from the final AIMessage
        final_message = all_messages[-1]
        
        if isinstance(final_message.content, str):
            answer = final_message.content
        elif isinstance(final_message.content, list):
            # En caso de que el mensaje devuelva una lista de contenidos (como en algunos modelos)
            answer = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in final_message.content])
        else:
            answer = str(final_message.content)
        
        logger.info(f"Answer generated successfully in {duration:.2f}s. Tokens: In={input_tokens}, Out={output_tokens}, Total={total_tokens}. Sources: {sources}")
        
        return QueryResponse(
            answer=answer, 
            sources=sources,
            duration=duration,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )
    except Exception as e:
        logger.exception("Error handling query request:")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
