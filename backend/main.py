from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.database import get_db
from sqlalchemy import text

app = FastAPI(
    title="NeuroTutor AI API",
    description="Core Intelligence Engine APIs for NeuroLearn Platform",
    version="1.0.0"
)

# CORS — allow Next.js frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task_type: str
    user_profile: dict
    learning_state: dict
    learning_pattern: dict
    task_input: dict

from engines.router import get_engine_response

@app.post("/api/engine/route")
def route_task(request: TaskRequest, db: Session = Depends(get_db)):
    """Core Intelligence Router: Parses task_type and routes to specific engines."""
    response_data = get_engine_response(request.model_dump(), db)
    return {"status": "success", "routed_engine": request.task_type, "output": response_data}

@app.get("/health")
async def health_check():
    return {"status": "NeuroTutor AI Core Engines are Healthy"}

@app.get("/api/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """Validates the Database Connection pool is active."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Database Connection is OK."}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}
