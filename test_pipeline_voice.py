"""
Day 2 test: real voice in, real voice out. No typing.

Press Enter to record your turn (5 seconds), it transcribes, sends to
the brain, and speaks the reply back through your speakers.

Run: python test_pipeline_voice.py
"""

from app.brain import get_agent_reply
from app.voice_out import speak
from app.voice_in import record_audio, transcribe_audio

def main():
    print("=== Saarthi voice test ===")
    print("Press Enter to start a 5-second recording each turn. Say 'quit' to exit.\n")

    history = []
    turn = 0

    opening = get_agent_reply([{"role": "user", "content": "[CALL CONNECTED - greet the customer and introduce yourself]"}])
    print(f"AGENT: {opening['reply']}")
    print(f"  [classification: {opening['classification']} | action: {opening['action_needed']}]")
    speak(opening["reply"], f"turn_{turn}.mp3")
    history.append({"role": "assistant", "content": opening["reply"]})

    while True:
        turn += 1
        input("\nPress Enter to speak your turn...")

        audio_path = record_audio(duration_seconds=5.0, output_path=f"mic_turn_{turn}.wav")
        user_text = transcribe_audio(audio_path)
        print(f"YOU (transcribed): {user_text}")

        if not user_text.strip():
            print("  [nothing heard, try again]")
            turn -= 1
            continue

        if "quit" in user_text.lower():
            break

        history.append({"role": "user", "content": user_text})
        result = get_agent_reply(history)

        print(f"\nAGENT: {result['reply']}")
        print(f"  [classification: {result['classification']} | reasoning: {result['reasoning']} | action: {result['action_needed']} | lang: {result['detected_language']}]")

        history.append({"role": "assistant", "content": result["reply"]})
        speak(result["reply"], f"turn_{turn}.mp3")

        if result["action_needed"] == "send_whatsapp":
            print("  >>> WOULD FIRE WHATSAPP HERE (Day 4 builds this for real)")
        elif result["action_needed"] == "schedule_callback":
            print("  >>> WOULD BOOK CALLBACK HERE (Day 4 builds this for real)")


if __name__ == "__main__":
    main()
