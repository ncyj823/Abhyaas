# Saarthi — AI Voice Sales Agent (ElevateBox assignment)

## Day 1 setup

```bash
cd saarthi
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt --break-system-packages
```

Copy `.env.example` to `.env` and paste your real keys:
```bash
copy .env.example .env
```

Then edit `.env` with your actual Groq / ElevenLabs / Deepgram keys.

## Run the test pipeline

```bash
python test_pipeline.py
```

Type as if you're the caller. The agent will:
- Reply naturally (Groq Llama-3.3-70B)
- Classify you Hot/Warm/Cold live
- Speak the reply out loud (check `turn_0.mp3`, `turn_1.mp3`, etc. in the folder)

Try messages like:
- "hi, I sell handmade jewelry" → should stay neutral, start discovering
- "what's the price and how soon can you start?" → should go HOT
- "sounds interesting but my brother handles the budget" → should go WARM
- "just checking things out, not really looking right now" → should go COLD

## What's next
- Day 2: swap typed input for real Deepgram streaming STT
- Day 3: wrap `brain.py` in a proper LangGraph state machine
- Day 4: FastMCP tools for WhatsApp + scheduler, fired async via Redis/RQ
- Day 5: wire in Twilio for real telephony (only once everything above works)
