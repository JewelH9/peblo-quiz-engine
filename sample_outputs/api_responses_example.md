# Sample API Responses

## POST /ingest
```json
{
  "message": "ingestion done",
  "chunks": [
    {
      "chunk_id": "SRC_4A3B2C1D_CH_01",
      "source_id": "SRC_4A3B2C1D",
      "grade": 1,
      "subject": "Math",
      "topic": "peblo pdf grade1 math numbers",
      "text": "Numbers help us count things..."
    }
  ]
}
```

## POST /generate-quiz?source_id=SRC_4A3B2C1D
```json
{
  "generated": 6,
  "questions": [
    {
      "question_id": "Q_A1B2C3D4",
      "question": "How many sides does a triangle have?",
      "type": "MCQ",
      "options": ["2", "3", "4", "5"],
      "answer": "3",
      "difficulty": "easy"
    }
  ]
}
```

## GET /quiz?topic=math&difficulty=easy
```json
{
  "questions": [
    {
      "question_id": "Q_A1B2C3D4",
      "question": "How many sides does a triangle have?",
      "type": "MCQ",
      "options": ["2", "3", "4", "5"],
      "answer": "3",
      "difficulty": "easy",
      "topic": "peblo pdf grade1 math numbers"
    }
  ]
}
```

## POST /submit-answer
Request:
```json
{
  "student_id": "S001",
  "question_id": "Q_A1B2C3D4",
  "selected_answer": "3"
}
```
Response:
```json
{
  "student_id": "S001",
  "question_id": "Q_A1B2C3D4",
  "selected_answer": "3",
  "is_correct": true,
  "correct_answer": "3"
}
```

## GET /student/S001/stats
```json
{
  "student_id": "S001",
  "total_answered": 10,
  "correct": 7,
  "incorrect": 3,
  "accuracy": 70.0
}
```
