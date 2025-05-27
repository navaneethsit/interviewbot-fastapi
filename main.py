from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import pandas as pd
import os
import io
import pdfplumber
import docx2txt
from dotenv import load_dotenv
import asyncio
from functools import partial

load_dotenv()
app = FastAPI()

excel_path = "resumes.xlsx"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit

# Ensure Excel file exists
def ensure_excel_file():
    if not os.path.exists(excel_path):
        df = pd.DataFrame(columns=["filename", "content"])
        df.to_excel(excel_path, index=False)

ensure_excel_file()

# Synchronous PDF extraction
def extract_text_from_pdf_sync(file):
    try:
        with pdfplumber.open(file) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

# Synchronous DOCX extraction
def extract_text_from_docx_sync(file):
    try:
        return docx2txt.process(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")

# Asynchronous wrappers
async def extract_text_from_pdf(file: UploadFile):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(extract_text_from_pdf_sync, file.file))

async def extract_text_from_docx(file: UploadFile):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(extract_text_from_docx_sync, file.file))

# Background task to save to Excel
def save_to_excel(filename: str, content: str):
    try:
        df = pd.read_excel(excel_path)
        new_row = {"filename": filename, "content": content}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(excel_path, index=False)
    except Exception as e:
        # Log error instead of raising, since this runs in the background
        print(f"Error saving to Excel: {str(e)}")

@app.post("/resumeUpload/")
async def resume_upload(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    try:
        # Check file size
        file_size = 0
        for chunk in file.file:
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

        # Reset file pointer to start
        await file.seek(0)

        # Extract content based on file type
        if file.content_type == "application/pdf":
            content = await extract_text_from_pdf(file)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            content = await extract_text_from_docx(file)
        elif file.content_type.startswith("text"):
            content = (await file.read()).decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Save to Excel in the background
        background_tasks.add_task(save_to_excel, file.filename, content)

        return {"message": "Resume uploaded and queued for processing"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))