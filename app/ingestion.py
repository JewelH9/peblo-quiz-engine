import io
import re
import uuid
import hashlib
import pdfplumber

from app.database import save_source, save_chunk


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """extract all text from pdf using pdfplumber"""
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def clean_text(text: str) -> str:
    """basic cleaning - remove extra whitespace and weird chars"""
    # remove multiple spaces
    text = re.sub(r' +', ' ', text)
    # remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def chunk_text(text: str, chunk_size: int = 400) -> list:
    """split text into chunks by words roughly"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0

    for word in words:
        current_chunk.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def guess_metadata(filename: str, text: str) -> dict:
    """
    try to guess grade, subject and topic from filename and text
    this is kinda basic and might not always work perfectly
    """
    filename_lower = filename.lower()
    
    # guess grade
    grade = None
    grade_match = re.search(r'grade(\d)', filename_lower)
    if grade_match:
        grade = int(grade_match.group(1))

    # guess subject
    subject = "General"
    if "math" in filename_lower or "numbers" in filename_lower:
        subject = "Math"
    elif "science" in filename_lower or "plants" in filename_lower:
        subject = "Science"
    elif "english" in filename_lower or "grammar" in filename_lower:
        subject = "English"

    # guess topic from filename (rough)
    topic = filename.replace(".pdf", "").replace("_", " ").strip()

    return {"grade": grade, "subject": subject, "topic": topic}


def ingest_pdf(pdf_bytes: bytes, filename: str) -> list:
    """
    main ingestion function
    returns list of chunk dicts that were saved
    """
    # generate source id from filename hash
    source_id = "SRC_" + hashlib.md5(filename.encode()).hexdigest()[:8].upper()

    # save source
    save_source(source_id, filename)

    # extract text
    raw_text = extract_text_from_pdf(pdf_bytes)
    cleaned = clean_text(raw_text)

    if not cleaned:
        return []

    # chunk
    chunks_text = chunk_text(cleaned)
    meta = guess_metadata(filename, cleaned)

    saved_chunks = []
    for i, chunk_text_part in enumerate(chunks_text):
        chunk_id = f"{source_id}_CH_{str(i+1).zfill(2)}"
        chunk = {
            "chunk_id": chunk_id,
            "source_id": source_id,
            "grade": meta["grade"],
            "subject": meta["subject"],
            "topic": meta["topic"],
            "text": chunk_text_part
        }
        save_chunk(chunk)
        saved_chunks.append(chunk)

    print(f"Ingested {len(saved_chunks)} chunks from {filename}")
    return saved_chunks
