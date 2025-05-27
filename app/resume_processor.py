import pdfplumber
import docx2txt
import asyncio
from fastapi import UploadFile, HTTPException
from functools import partial

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Extract PDF content (sync)
def extract_pdf(file):
    try:
        with pdfplumber.open(file) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {str(e)}")

# Extract DOCX content (sync)
def extract_docx(file):
    try:
        return docx2txt.process(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX read error: {str(e)}")

# Master async extractor
async def extract_resume_text(file: UploadFile) -> str:
    content_type = file.content_type
    size = 0

    # File size check
    for chunk in file.file:
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    await file.seek(0)

    if content_type == "application/pdf":
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(extract_pdf, file.file))

    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(extract_docx, file.file))

    elif content_type.startswith("text"):
        return (await file.read()).decode("utf-8")

    raise HTTPException(status_code=400, detail="Unsupported file type")
