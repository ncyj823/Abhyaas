"""
Converts the agent's text reply into speech using ElevenLabs.
Day 1: saves to an mp3 file so you can listen and confirm it sounds right.
Day 2+: this gets swapped for streaming audio directly into the call.
"""

import os
import simpleaudio as sa
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Default multilingual voice - swap this after browsing ElevenLabs voice library
# for one that handles Hindi/Telugu well. "eleven_multilingual_v2" model supports both.
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # "Sarah" - premade, free-tier compatible


def speak(text: str, output_path: str = "output.mp3", play: bool = True) -> str:
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="pcm_16000",  # raw PCM so we can play it directly
    )

    audio_bytes = b"".join(audio)

    if play:
        play_obj = sa.play_buffer(audio_bytes, num_channels=1, bytes_per_sample=2, sample_rate=16000)
        play_obj.wait_done()

    # also save a copy for the record
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    return output_path
