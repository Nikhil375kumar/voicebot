"""
VoiceBot – Main Streamlit App
=============================
Run:  streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64
import time

from config.persona import PERSONA
from services.groq_service import transcribe_audio, get_llm_response

# ── env ──────────────────────────────────────────────────────────────────────
load_dotenv()

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"VoiceBot · {PERSONA['name']}",
    page_icon="🎙️",
    layout="centered",
)

# ── custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Dark background */
[data-testid="stAppViewContainer"] { background: #0f172a; }
[data-testid="stHeader"] { background: transparent; }

/* Chat bubbles */
.user-bubble {
    background: #4f46e5;
    color: #fff;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 16px;
    margin: 6px 0;
    max-width: 80%;
    margin-left: auto;
    text-align: right;
}
.bot-bubble {
    background: #1e293b;
    color: #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 10px 16px;
    margin: 6px 0;
    max-width: 80%;
    border: 1px solid #334155;
}
.chip {
    display: inline-block;
    background: #1e293b;
    color: #a5b4fc;
    border: 1px solid #4f46e5;
    border-radius: 999px;
    padding: 6px 14px;
    margin: 4px;
    font-size: 0.82rem;
    cursor: pointer;
}
.section-title {
    color: #94a3b8;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
h1, h2, h3 { color: #f1f5f9 !important; }
p { color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)

# ── session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # list of {"role": "user"|"bot", "text": str}
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None  # base64 audio to play after rerun

# ── helper: generate audio base64 (does NOT play — just returns bytes) ────────
def generate_audio_b64(text: str):
    """Generate gTTS audio and return as base64 string. Returns None on failure."""
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception:
        return None

# ── helper: render audio player (call DURING render, never before st.rerun) ──
def render_audio(audio_b64: str):
    """Inject autoplay audio HTML. Must be called during the render phase."""
    uid = int(time.time() * 1000)
    st.components.v1.html(f"""
        <audio id="tts_{uid}" autoplay style="display:none">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        </audio>
        <script>
            var a = document.getElementById('tts_{uid}');
            if (a) a.play().catch(function(){{}});
        </script>
    """, height=0)

# ── helper: process a question (text or transcribed) ─────────────────────────
def process_question(question: str):
    if not question.strip():
        return
    st.session_state.messages.append({"role": "user", "text": question})
    with st.spinner("🤔 Thinking..."):
        reply = get_llm_response(question, PERSONA["system_prompt"])
    st.session_state.messages.append({"role": "bot", "text": reply})
    # ✅ Store audio in session_state — will be played AFTER st.rerun() during render
    st.session_state.pending_audio = generate_audio_b64(reply)

# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

# ── header ───────────────────────────────────────────────────────────────────
st.markdown(f"## 🎙️ VoiceBot · *{PERSONA['name']}*")
st.markdown(f"<p style='margin-top:-12px;color:#94a3b8'>{PERSONA['role']} · Powered by <b>Groq + Llama 3.3</b></p>", unsafe_allow_html=True)
st.divider()

# ── chat transcript ───────────────────────────────────────────────────────────
if st.session_state.messages:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-bubble'>🧑 {msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-bubble'>🤖 {msg['text']}</div>", unsafe_allow_html=True)

    # ✅ Play pending audio DURING render (after rerun) so st.rerun() doesn't cut it off
    if st.session_state.pending_audio:
        render_audio(st.session_state.pending_audio)
        st.session_state.pending_audio = None  # clear after playing

    if st.button("🗑️ Clear conversation", use_container_width=False):
        st.session_state.messages = []
        st.session_state.pending_audio = None
        st.rerun()
else:
    st.markdown("<p style='text-align:center;color:#475569;padding:40px 0'>Start by clicking the mic or choosing a question below 👇</p>", unsafe_allow_html=True)

st.divider()

# ── voice input ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🎤 Speak your question</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#ef4444",
        neutral_color="#4f46e5",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0,
        key="mic",
    )

if audio_bytes and len(audio_bytes) > 1000:
    # Avoid re-processing same recording across reruns
    audio_hash = hash(audio_bytes)
    if st.session_state.get("last_audio_hash") != audio_hash:
        st.session_state["last_audio_hash"] = audio_hash
        # Step 1: Transcribe audio → text
        transcript = None
        with st.spinner("🎧 Transcribing audio..."):
            try:
                transcript = transcribe_audio(audio_bytes)
            except Exception as e:
                st.error(f"❌ Transcription error: {e}")
        # Step 2: Send transcript to LLM (only if STT succeeded)
        if transcript and transcript.strip():
            # Reject transcripts that are too short or look like noise
            clean = transcript.strip()
            if len(clean) < 4:
                st.warning(f"⚠️ Couldn't understand: \"{clean}\" — please speak more clearly.")
            else:
                try:
                    process_question(clean)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ LLM error: {e}")

# ── sample questions ──────────────────────────────────────────────────────────
st.markdown("<div class='section-title' style='margin-top:16px'>💡 Or click a question</div>", unsafe_allow_html=True)

cols = st.columns(2)
for i, q in enumerate(PERSONA["sample_questions"]):
    with cols[i % 2]:
        if st.button(q, key=f"q_{i}", use_container_width=True):
            process_question(q)
            st.rerun()

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:#334155;font-size:0.8rem'>"
    f"Built by {PERSONA['name']} · React-free · Groq API · Web Speech Synthesis</p>",
    unsafe_allow_html=True
)
