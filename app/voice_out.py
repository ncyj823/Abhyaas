"""
Converts the agent's text reply into speech using ElevenLabs.
Day 1: saves to an mp3 file so you can listen and confirm it sounds right.
Day 2+: this gets swapped for streaming audio directly into the call.
"""

import os
import wave
import winsound
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Default multilingual voice - swap this after browsing ElevenLabs voice library
# for one that handles Hindi/Telugu well. "eleven_multilingual_v2" model supports both.
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # "Sarah" - premade, free-tier compatible


def speak(text: str, output_path: str = "output.wav", play: bool = True) -> str:
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="pcm_16000",  # raw PCM, we wrap it into a WAV ourselves
    )

    audio_bytes = b"".join(audio)

    # winsound can only play proper WAV files, so wrap the raw PCM in a WAV header
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
        wf.setframerate(16000)
        wf.writeframes(audio_bytes)

    if play:
        winsound.PlaySound(output_path, winsound.SND_FILENAME)

    return output_path
