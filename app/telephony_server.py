"""
Day 5: real telephony. Twilio connects to this WebSocket endpoint during
a live call, streaming audio in both directions as base64-encoded mulaw
(8kHz) chunks - very different from the local mic/speaker setup in
Day 1-4, so this is a new module, not a reuse of voice_in.py/voice_out.py.

Flow per call:
1. Twilio dials out (via outbound_call.py), connects the call audio to
   this WebSocket via a <Stream> TwiML instruction.
2. Audio chunks arrive here -> buffered -> sent to Deepgram for
   transcription (via websocket streaming, not the batch mode we used
   for mic testing).
3. Once we have a transcript chunk, it goes to the LangGraph pipeline
   (app/graph.py) - same brain, same classification logic as Day 1-4.
4. The reply text goes to ElevenLabs -> streamed back as audio chunks
   -> sent back over this same WebSocket to Twilio -> caller hears it.

Run with: uvicorn app.telephony_server:app --host 0.0.0.0 --port 8000
Then expose via ngrok: ngrok http 8000
"""

import os
import json
import base64
import audioop
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from app.graph import run_turn
from elevenlabs.client import ElevenLabs
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
)

load_dotenv()

app = FastAPI()

deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah


@app.post("/voice")
async def voice_webhook():
    """
    Twilio hits this URL when the call connects. Returns TwiML that tells
    Twilio to open a Media Stream WebSocket to our /media-stream endpoint.
    """
    ngrok_host = os.getenv("NGROK_HOST", "your-ngrok-url.ngrok-free.app")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{ngrok_host}/media-stream" />
    </Connect>
</Response>"""
    return PlainTextResponse(content=twiml, media_type="text/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    print("Twilio connected to media stream")

    history = [{"role": "user", "content": "[CALL CONNECTED - greet the customer and introduce yourself]"}]
    stream_sid = None

    # --- Send opening greeting immediately ---
    state = run_turn(history)
    history = state["history"]
    await speak_over_stream(websocket, state["reply"], stream_sid)

    # --- Set up Deepgram live transcription ---
    dg_connection = deepgram.listen.websocket.v("1")

    transcript_buffer = {"text": ""}

    def on_transcript(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if sentence and result.is_final:
            transcript_buffer["text"] += " " + sentence

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)

    options = LiveOptions(
        model="nova-2",
        encoding="mulaw",
        sample_rate=8000,
        channels=1,
        smart_format=True,
        interim_results=True,
        endpointing=500,  # ms of silence before considering a turn "done"
    )
    dg_connection.start(options)

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data["event"] == "start":
                stream_sid = data["start"]["streamSid"]
                print(f"Stream started: {stream_sid}")

            elif data["event"] == "media":
                audio_payload = base64.b64decode(data["media"]["payload"])
                dg_connection.send(audio_payload)

                # Check if we have a completed transcript to act on
                if transcript_buffer["text"].strip():
                    user_text = transcript_buffer["text"].strip()
                    transcript_buffer["text"] = ""

                    history.append({"role": "user", "content": user_text})
                    state = run_turn(history)
                    history = state["history"]

                    await speak_over_stream(websocket, state["reply"], stream_sid)

                    if state["action_needed"] == "send_whatsapp":
                        print(f"  >>> WhatsApp action taken: {state['action_taken']}")

            elif data["event"] == "stop":
                print("Call ended")
                break

    except WebSocketDisconnect:
        print("Twilio disconnected")
    finally:
        dg_connection.finish()


async def speak_over_stream(websocket: WebSocket, text: str, stream_sid: str):
    """
    Converts text to speech and streams it back to Twilio as base64
    mulaw audio chunks over the same WebSocket.
    """
    audio = elevenlabs.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="pcm_16000",
    )
    pcm_bytes = b"".join(audio)

    # Convert 16kHz PCM -> 8kHz mulaw (what Twilio expects)
    downsampled, _ = audioop.ratecv(pcm_bytes, 2, 1, 16000, 8000, None)
    mulaw_bytes = audioop.lin2ulaw(downsampled, 2)

    payload = base64.b64encode(mulaw_bytes).decode("utf-8")

    if stream_sid:
        media_message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {"payload": payload},
        }
        await websocket.send_text(json.dumps(media_message))
