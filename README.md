# Saarthi

An AI voice sales agent that places real outbound calls, holds a natural 
sales conversation in English, Hindi, or Telugu, and reads buyer intent 
live — classifying each lead as Hot, Warm, or Cold as the conversation 
unfolds. On a Hot signal, it fires a WhatsApp message mid-call with 
context from what was actually discussed. On Warm, it books a callback 
from spoken time references like "call me back tomorrow morning."

Built for the ElevateBox SDE Intern assignment — a system judged purely 
on whether the call works, live, on the first attempt.

**Stack**: FastAPI · LangGraph · Groq (Llama/GPT-OSS) · Deepgram (STT) · 
ElevenLabs (TTS) · Twilio (telephony) · Redis/RQ (async mid-call actions) · FastMCP
