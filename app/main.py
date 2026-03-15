from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

from app.ingestion import ingest_pdf
from app.quiz_gen import generate_quiz_questions
from app.database import init_db, get_all_questions, save_answer, get_student_stats
from app.adaptive import get_next_difficulty

app = FastAPI(title="Peblo Quiz Engine")

# initialize db on startup
@app.on_event("startup")
def startup():
    init_db()

# --- models ---

class AnswerSubmit(BaseModel):
    student_id: str
    question_id: str
    selected_answer: str


# --- routes ---

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """Upload a PDF and extract content from it"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="only pdf files allowed")
    
    content = await file.read()
    result = ingest_pdf(content, file.filename)
    return {"message": "ingestion done", "chunks": result}


@app.post("/generate-quiz")
def generate_quiz(source_id: str):
    """Generate quiz questions for a given source_id"""
    questions = generate_quiz_questions(source_id)
    if not questions:
        raise HTTPException(status_code=404, detail="no chunks found for this source")
    return {"generated": len(questions), "questions": questions}


@app.get("/quiz")
def get_quiz(topic: Optional[str] = None, difficulty: Optional[str] = None, student_id: Optional[str] = None):
    """Get quiz questions, optionally filter by topic and difficulty"""
    # if student_id given, try to adapt difficulty
    if student_id and not difficulty:
        difficulty = get_next_difficulty(student_id)

    questions = get_all_questions(topic=topic, difficulty=difficulty)
    if not questions:
        return {"message": "no questions found", "questions": []}
    return {"questions": questions}


@app.post("/submit-answer")
def submit_answer(payload: AnswerSubmit):
    """Submit a student answer"""
    result = save_answer(
        student_id=payload.student_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer
    )
    return result


@app.get("/student/{student_id}/stats")
def student_stats(student_id: str):
    stats = get_student_stats(student_id)
    return stats


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
