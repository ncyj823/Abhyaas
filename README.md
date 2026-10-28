# Abhyaas — Voice Sales-Call Practice Tool

Practice sales calls with AI customers who speak Telugu-English, Hinglish, or English. Uncover hidden facts, read buying intent, and get scored.

> **Phase 1 complete** — persona engine, reveal logic, CLI chat, and tests.

## Quick Start (PowerShell)

```powershell
cd Saarthi
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Copy and fill in your Groq API key
copy .env.example .env
# Edit .env with your GROQ_API_KEY

# Run tests (no API key needed)
python -m pytest tests\ -v

# CLI chat (needs GROQ_API_KEY in .env)
python -m app.cli
python -m app.cli --debug          # shows revealed facts after each turn
python -m app.cli --persona te_hot_candles
```

## Personas

| ID | Name | Business | Language | Intent |
|----|------|----------|----------|--------|
| te_hot_candles | Ravi Kumar | Candles & Home Decor | Telugu-English | HOT |
| te_warm_sarees | Anjali Reddy | Handloom Sarees | Telugu-English | WARM |
| hi_hot_electronics | Priya Sharma | Electronics Repair | Hinglish | HOT |
| hi_cold_pickles | Munna Bhai | Pickles & Papad | Hinglish | COLD |
| en_warm_bakery | David Thomas | Artisan Bakery | English | WARM |
| en_cold_gym | Sneha Iyer | Gym Equipment Rental | English | COLD |
