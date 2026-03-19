from flask import Flask, request
from faster_whisper import WhisperModel
from gtts import gTTS
from twilio.rest import Client
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = Flask(__name__)

# Load whisper model once at startup (small = fast)
print("Loading Whisper model...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
print("Whisper ready!")

conversation_history = []

def transcribe_audio(audio_url):
    """Download and transcribe the caller's audio locally"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    # Download the recording from Twilio
    response = requests.get(audio_url, auth=(account_sid, auth_token))
    audio_path = "temp_recording.wav"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    # Transcribe locally with Whisper
    segments, _ = whisper_model.transcribe(audio_path, beam_size=1)
    text = " ".join([s.text for s in segments])
    return text.strip()


def ask_ollama(user_text):
    """Send text to Ollama and get AI reply"""
    conversation_history.append({
        "role": "user",
        "content": user_text
    })

    response = requests.post("http://localhost:11434/api/chat", json={
        "model": "llama3.2",
        "messages": [
            {
                "role": "system",
                "content": """You are a friendly AI phone assistant.
                Keep ALL responses under 2 sentences — this is a phone call.
                Ask the caller their name and reason for calling.
                Be warm and natural."""
            }
        ] + conversation_history,
        "stream": False
    })

    reply = response.json()["message"]["content"]
    conversation_history.append({
        "role": "assistant",
        "content": reply
    })
    return reply


def inject_audio_to_call(call_sid, filename):
    """Tell Node server the AI reply is ready"""
    public_url = os.getenv("PUBLIC_URL")
    audio_url = f"{public_url}/static/{filename}"
    
    # Notify Node that reply is ready
    requests.post("http://127.0.0.1:3000/ai-ready", json={
        "callSid": call_sid,
        "audioUrl": audio_url
    })
    print(f"Audio ready: {audio_url}")


@app.route("/handle-recording-done", methods=["POST"])
def handle_recording_done():
    """Twilio calls this when recording is ready — much faster than transcription"""
    recording_url = request.form.get("RecordingUrl", "")
    call_sid = request.form.get("CallSid", "")

    print(f"Recording received, transcribing...")

    # Transcribe locally (fast!)
    transcript = transcribe_audio(recording_url)
    print(f"Caller said: {transcript}")

    if not transcript:
        return "", 200

    # Get AI reply
    ai_reply = ask_ollama(transcript)
    print(f"AI reply: {ai_reply}")

    # Convert to audio
    os.makedirs("static", exist_ok=True)
    audio_filename = f"reply_{call_sid}.mp3"
    tts = gTTS(text=ai_reply, lang="en", slow=False)
    tts.save(f"static/{audio_filename}")

    # Play back to caller
    inject_audio_to_call(call_sid, audio_filename)

    return "", 200


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(port=5001)