# Peblo AI Backend Engineer Challenge

## What This Project Does

This is a mini content ingestion and adaptive quiz engine built for the Peblo backend challenge. It takes PDF files of educational content, extracts text from them, and uses an LLM (Anthropic Claude) to generate quiz questions automatically. Students can answer questions and the system adjusts difficulty based on their performance.

---

## Architecture

```
PDF Upload
    ↓
/ingest endpoint
    ↓
pdfplumber extracts text
    ↓
Text cleaned and chunked (~400 chars per chunk)
    ↓
Chunks saved to SQLite database
    ↓
/generate-quiz endpoint
    ↓
Each chunk sent to Claude API with prompt
    ↓
Claude returns MCQ / True-False / Fill-in-blank questions
    ↓
Questions saved with link back to source chunk
    ↓
/quiz endpoint serves questions (filter by topic/difficulty)
    ↓
Student submits answer via /submit-answer
    ↓
System checks correctness, saves result
    ↓
Adaptive logic adjusts difficulty for next quiz
```

### Database Schema

- **sources** - tracks uploaded PDF files
- **chunks** - extracted text segments from each PDF
- **questions** - generated quiz questions (linked to chunks)
- **student_answers** - student submissions and correctness

---

## Tech Stack

- **Python 3.10+**
- **FastAPI** - for the REST API
- **SQLite** - simple database (can be swapped for postgres)
- **pdfplumber** - PDF text extraction
- **Anthropic Claude API** - quiz question generation
- **uvicorn** - ASGI server

---

## Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/peblo-quiz-engine.git
cd peblo-quiz-engine
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # on windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy the example file and fill in your API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
LLM_API_KEY=your_anthropic_api_key_here
DATABASE_URL=peblo.db
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

You can also view the auto-generated API docs at `http://localhost:8000/docs`

---

## How to Test the Endpoints

### Step 1 - Ingest a PDF

```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@peblo_pdf_grade1_math_numbers.pdf"
```

Note down the `source_id` from the response (e.g. `SRC_4A3B2C1D`)

### Step 2 - Generate quiz questions

```bash
curl -X POST "http://localhost:8000/generate-quiz?source_id=SRC_4A3B2C1D"
```

### Step 3 - Get quiz questions

```bash
curl "http://localhost:8000/quiz?topic=math&difficulty=easy"
```

### Step 4 - Submit an answer

```bash
curl -X POST "http://localhost:8000/submit-answer" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "S001", "question_id": "Q_A1B2C3D4", "selected_answer": "3"}'
```

### Step 5 - Check student stats

```bash
curl "http://localhost:8000/student/S001/stats"
```

---

## Adaptive Difficulty Logic

The system looks at the last 5 answers from a student:
- If 4 or more correct → increase difficulty
- If 2 or less correct → decrease difficulty
- Otherwise → keep same difficulty

Difficulty levels: easy → medium → hard

When calling `/quiz` with a student_id, the system automatically picks the right difficulty level for them.

---

## Sample Outputs

Check the `sample_outputs/` folder:
- `extracted_content_example.json` - what chunks look like
- `generated_questions_example.json` - what generated questions look like
- `api_responses_example.md` - example API request/response pairs

---

## Notes / Limitations

- The metadata detection (grade, subject, topic) is based on filename parsing and is pretty basic. Could be improved with NLP.
- SQLite is used for simplicity. For production PostgreSQL would be better.
- Error handling could be more robust in some places.
- The LLM sometimes generates slightly inconsistent JSON so I added a fallback parser.

---

## Folder Structure

```
peblo-quiz-engine/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app and routes
│   ├── ingestion.py     # PDF extraction and chunking
│   ├── quiz_gen.py      # LLM quiz generation
│   ├── database.py      # SQLite database logic
│   └── adaptive.py      # Adaptive difficulty logic
├── sample_outputs/
│   ├── extracted_content_example.json
│   ├── generated_questions_example.json
│   └── api_responses_example.md
├── requirements.txt
├── .env.example
└── README.md
```
