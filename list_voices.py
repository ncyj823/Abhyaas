"""
Run this once to see which voices are actually usable on your free-tier API key.
python list_voices.py
"""

import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

voices = client.voices.get_all()
for v in voices.voices:
    print(f"{v.name}: {v.voice_id}  (category: {v.category})")
