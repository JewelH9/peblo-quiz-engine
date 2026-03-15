from app.database import get_conn


DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


def get_next_difficulty(student_id: str) -> str:
    """
    Simple adaptive logic:
    - look at last 5 answers
    - if 4+ correct -> go harder
    - if 2 or less correct -> go easier
    - else stay same
    """
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT sa.is_correct, q.difficulty
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.question_id
        WHERE sa.student_id = ?
        ORDER BY sa.submitted_at DESC
        LIMIT 5
        """,
        (student_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return "easy"  # new student starts easy

    recent_answers = [dict(r) for r in rows]
    correct_count = sum(1 for a in recent_answers if a["is_correct"])
    total = len(recent_answers)

    # get current difficulty from most recent question
    current_difficulty = recent_answers[0]["difficulty"] if recent_answers else "easy"

    if current_difficulty not in DIFFICULTY_LEVELS:
        current_difficulty = "easy"

    current_index = DIFFICULTY_LEVELS.index(current_difficulty)

    # adjust based on performance
    if correct_count >= 4 and current_index < 2:
        # doing well, increase difficulty
        return DIFFICULTY_LEVELS[current_index + 1]
    elif correct_count <= 2 and current_index > 0:
        # struggling, decrease difficulty
        return DIFFICULTY_LEVELS[current_index - 1]
    else:
        return current_difficulty
