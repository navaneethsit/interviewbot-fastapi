from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import io, os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class TextRequest(BaseModel):
    text: str

@app.post("/ask/")
async def ask_and_get_audio_response(request: TextRequest):
    try:
        # Limit response tokens to reduce generation time
        chat_response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # Use this if available
    messages=[
        {"role": "system", "content": "Answer briefly and professionally."},
        {"role": "user", "content": request.text}
    ],
    max_tokens=50,
    temperature=0.5
)

        answer = chat_response.choices[0].message.content.strip()

        # Try a faster voice like "echo" or "nova"
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="echo",  # Try different voices for faster TTS
            input=answer,
        )

        audio_data = tts_response.read()
        audio_stream = io.BytesIO(audio_data)
        audio_stream.seek(0)

        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=answer.mp3"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
