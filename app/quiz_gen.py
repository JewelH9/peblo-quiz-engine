import os
import json
import uuid
import google.generativeai as genai

from app.database import get_chunks_by_source, save_question

genai.configure(api_key=os.getenv("LLM_API_KEY"))


def build_prompt(chunk_text: str, topic: str) -> str:
    return f"""
You are an educational quiz generator. Given the following text from a learning material, generate 3 quiz questions.

Text:
{chunk_text}

Generate exactly 3 questions in this JSON array format. Make sure types are varied - include MCQ, true_false, and fill_in_blank.

Return ONLY a valid JSON array, no other text:
[
  {{
    "question": "...",
    "type": "MCQ",
    "options": ["A", "B", "C", "D"],
    "answer": "correct option",
    "difficulty": "easy|medium|hard"
  }},
  {{
    "question": "...",
    "type": "true_false",
    "options": ["True", "False"],
    "answer": "True or False",
    "difficulty": "easy|medium|hard"
  }},
  {{
    "question": "...",
    "type": "fill_in_blank",
    "options": [],
    "answer": "the answer word",
    "difficulty": "easy|medium|hard"
  }}
]
"""


def generate_quiz_questions(source_id: str) -> list:
    """generate quiz questions for all chunks of a source"""
    chunks = get_chunks_by_source(source_id)

    if not chunks:
        return []

    all_questions = []

    for chunk in chunks:
        try:
            prompt = build_prompt(chunk["text"], chunk.get("topic", ""))

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()

            # sometimes llm adds backticks so lets remove them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            questions_data = json.loads(raw)

            for q in questions_data:
                q_id = "Q_" + uuid.uuid4().hex[:8].upper()
                question_record = {
                    "question_id": q_id,
                    "source_chunk_id": chunk["chunk_id"],
                    "question": q["question"],
                    "type": q["type"],
                    "options": q.get("options", []),
                    "answer": q["answer"],
                    "difficulty": q.get("difficulty", "medium"),
                    "topic": chunk.get("topic", "")
                }
                save_question(question_record)
                all_questions.append(question_record)

        except json.JSONDecodeError as e:
            print(f"JSON parse error for chunk {chunk['chunk_id']}: {e}")
            continue
        except Exception as e:
            print(f"Error generating for chunk {chunk['chunk_id']}: {e}")
            continue

    return all_questions
