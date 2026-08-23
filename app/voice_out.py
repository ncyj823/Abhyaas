"""
Converts the agent's text reply into speech using ElevenLabs.
Day 1: saves to an mp3 file so you can listen and confirm it sounds right.
Day 2+: this gets swapped for streaming audio directly into the call.
"""

import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Default multilingual voice - swap this after browsing ElevenLabs voice library
# for one that handles Hindi/Telugu well. "eleven_multilingual_v2" model supports both.
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # "Sarah" - premade, free-tier compatible


def speak(text: str, output_path: str = "output.mp3") -> str:
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text,
    )

    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return output_path
