from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import io
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class TextRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Interview Bot API"}

@app.post("/ask/")
async def ask_and_get_audio_response(request: TextRequest):
    try:
        
        chat_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": request.text}]
    )
    except openai.error.OpenAIError as e:
        print("Error calling OpenAI:", e)

        answer = chat_response.choices[0].message.content

        
        tts_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=answer
    )

        audio_data = tts_response.read()

        
        audio_stream = io.BytesIO(audio_data)
        audio_stream.seek(0)

        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=answer.mp3"}
        )

    except Exception as e:
        print(f"Error occurred: {e}") 
        raise HTTPException(status_code=500, detail=str(e))
