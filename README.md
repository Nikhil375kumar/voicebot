# 🎙️ VoiceBot

A personal AI voice assistant built with **Streamlit + Groq**. It listens to your voice, transcribes it with Whisper, generates a response with Llama 3.3, and speaks it back using the browser's built-in TTS — all in a single-page app.

## 📁 Folder Structure

```
voicebot/
├── app.py                  ← Main Streamlit app (run this)
├── config/
│   └── persona.py          ← All persona data (edit to customize)
├── services/
│   └── groq_service.py     ← Groq API calls (STT + LLM)
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Local Setup

```bash
# 1. Clone / download the project
cd voicebot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Groq API key (free at console.groq.com)
cp .env.example .env
# Edit .env and paste your key

# 4. Run
streamlit run app.py
```

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Free API key from [console.groq.com](https://console.groq.com) |

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo and set `app.py` as the entry point
4. Under **Secrets**, add: `GROQ_API_KEY = "your_key_here"`
5. Deploy → get a public URL ✅

## 🔄 How It Works

```
User clicks mic → Audio recorded → Groq Whisper (STT) → 
Groq Llama 3.3 (LLM) → Text reply → Browser Speech Synthesis (TTS) → User hears
```
