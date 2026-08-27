"""
Day 2: real speech input. Records a few seconds of your mic audio,
sends it to Deepgram, returns the transcript.

This is BATCH mode (record -> send -> get transcript back), not true
live streaming yet. That's intentional - batch is far more reliable to
get working first. Real streaming (needed for mid-call WhatsApp firing
before the call ends) comes when we wire in Twilio Media Streams on Day 5,
which handles audio very differently from a local mic anyway.
"""

import os
import wave
import sounddevice as sd
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from dotenv import load_dotenv

load_dotenv()

deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

SAMPLE_RATE = 16000  # Deepgram prefers 16kHz for speech


def record_audio(duration_seconds: float = 5.0, output_path: str = "mic_input.wav") -> str:
    print(f"  [recording for {duration_seconds}s... speak now]")
    audio = sd.rec(
        int(duration_seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    print("  [recording done]")
    return output_path


def transcribe_audio(file_path: str, language: str = None) -> str:
    """
    language: None lets Deepgram auto-detect. You can force "hi" or "te"
    if auto-detect struggles with code-switching.
    """
    with open(file_path, "rb") as f:
        buffer_data = f.read()

    payload: FileSource = {"buffer": buffer_data}

    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
        detect_language=(language is None),
        language=language,
    )

    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
    transcript = response.results.channels[0].alternatives[0].transcript
    return transcript
