from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import openai
import io
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY").strip())

app = FastAPI()

class TextRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Interview Bot API"}

@app.post("/ask/")
async def ask_and_get_audio_response(request: TextRequest):
    try:
        # Get chat response
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": request.text}]
        )
        answer = chat_response.choices[0].message.content

        # Convert to speech
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=answer
        )
        audio_data = tts_response.read()

        # Stream audio back
        audio_stream = io.BytesIO(audio_data)
        audio_stream.seek(0)

        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=answer.mp3"}
        )

    except openai.OpenAIError as e:
        print("OpenAI API error:", e)
        raise HTTPException(status_code=500, detail="OpenAI API error")

    except Exception as e:
        print("Unhandled error:", e)
        raise HTTPException(status_code=500, detail=str(e))
