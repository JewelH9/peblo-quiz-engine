import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "peblo.db")
DB_PATH = os.path.normpath(DB_PATH)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # source documents table
    c.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            filename TEXT,
            created_at TEXT
        )
    """)

    # content chunks
    c.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            source_id TEXT,
            grade INTEGER,
            subject TEXT,
            topic TEXT,
            text TEXT,
            FOREIGN KEY (source_id) REFERENCES sources(source_id)
        )
    """)

    # quiz questions
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id TEXT PRIMARY KEY,
            source_chunk_id TEXT,
            question TEXT,
            type TEXT,
            options TEXT,
            answer TEXT,
            difficulty TEXT,
            topic TEXT,
            FOREIGN KEY (source_chunk_id) REFERENCES chunks(chunk_id)
        )
    """)

    # student answers
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            question_id TEXT,
            selected_answer TEXT,
            is_correct INTEGER,
            submitted_at TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(question_id)
        )
    """)

    conn.commit()
    conn.close()
    print("DB initialized!")


def save_source(source_id, filename):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sources VALUES (?, ?, ?)",
        (source_id, filename, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def save_chunk(chunk):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO chunks VALUES (?, ?, ?, ?, ?, ?)",
        (chunk["chunk_id"], chunk["source_id"], chunk.get("grade"), chunk.get("subject"), chunk.get("topic"), chunk["text"])
    )
    conn.commit()
    conn.close()


def get_chunks_by_source(source_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM chunks WHERE source_id = ?", (source_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_question(q):
    conn = get_conn()
    options_json = json.dumps(q.get("options", []))
    conn.execute(
        "INSERT OR IGNORE INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (q["question_id"], q["source_chunk_id"], q["question"], q["type"], options_json, q["answer"], q["difficulty"], q.get("topic", ""))
    )
    conn.commit()
    conn.close()


def get_all_questions(topic=None, difficulty=None):
    conn = get_conn()
    query = "SELECT * FROM questions WHERE 1=1"
    params = []

    if topic:
        query += " AND topic LIKE ?"
        params.append(f"%{topic}%")
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        q = dict(r)
        # parse options back from json string
        try:
            q["options"] = json.loads(q["options"])
        except:
            q["options"] = []
        result.append(q)
    return result


def save_answer(student_id, question_id, selected_answer):
    conn = get_conn()
    # get correct answer
    row = conn.execute("SELECT answer FROM questions WHERE question_id = ?", (question_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "question not found"}

    correct_answer = row["answer"].strip().lower()
    is_correct = 1 if selected_answer.strip().lower() == correct_answer else 0

    conn.execute(
        "INSERT INTO student_answers (student_id, question_id, selected_answer, is_correct, submitted_at) VALUES (?, ?, ?, ?, ?)",
        (student_id, question_id, selected_answer, is_correct, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {
        "student_id": student_id,
        "question_id": question_id,
        "selected_answer": selected_answer,
        "is_correct": bool(is_correct),
        "correct_answer": row["answer"]
    }


def get_student_stats(student_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM student_answers WHERE student_id = ? ORDER BY submitted_at DESC",
        (student_id,)
    ).fetchall()
    conn.close()

    total = len(rows)
    correct = sum(1 for r in rows if r["is_correct"])
    return {
        "student_id": student_id,
        "total_answered": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy": round(correct / total * 100, 2) if total > 0 else 0
    }
