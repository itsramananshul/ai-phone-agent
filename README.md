# AI Phone Agent

An AI that answers your phone calls and talks back like a human.
Runs completely free on your local machine.

## Stack
- Twilio (phone number + call handling)
- Node.js + Express (webhook server)
- Python + Flask (AI processing)
- Ollama + LLaMA 3.2 (free local AI)
- Faster-Whisper (speech to text)
- gTTS (text to speech)
- ngrok (expose localhost)

## Setup

### 1. Clone the repo
git clone https://github.com/itsramananshul/ai-phone-agent

### 2. Install Node dependencies
npm install

### 3. Install Python dependencies
pip install flask faster-whisper gtts twilio python-dotenv requests

### 4. Install Ollama
Download from ollama.com and run:
ollama pull llama3.2

### 5. Create your .env file
Copy .env.example and fill in your values:
cp .env.example .env

### 6. Run everything
Terminal 1: ollama serve (or it runs automatically on Windows)
Terminal 2: node server.js
Terminal 3: python ai_responder.py
Terminal 4: ngrok http 3000

## Cost
$1/month for Twilio number. Everything else is free.


## Step 7 — Create `.env.example`


TWILIO_ACCOUNT_SID=your_twilio_account_sid_here

TWILIO_AUTH_TOKEN=your_twilio_auth_token_here

PUBLIC_URL=your_ngrok_url_here

PORT=3000
