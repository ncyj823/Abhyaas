"""
Day 1 test: no real call, no real STT yet.
You type what the "caller" says, the agent brain responds + classifies,
and ElevenLabs speaks the reply out loud (saved as output.mp3 each turn).

Run: python test_pipeline.py
"""

from app.brain import get_agent_reply
from app.voice_out import speak

def main():
    print("=== Saarthi test pipeline ===")
    print("Type as the caller. Type 'quit' to exit.\n")

    history = []
    turn = 0

    # Kick off the call with the agent's opening line
    opening = get_agent_reply([{"role": "user", "content": "[CALL CONNECTED - greet the customer and introduce yourself]"}])
    print(f"AGENT: {opening['reply']}")
    print(f"  [classification: {opening['classification']} | action: {opening['action_needed']}]")
    speak(opening["reply"], f"turn_{turn}.mp3")
    history.append({"role": "assistant", "content": opening["reply"]})

    while True:
        turn += 1
        user_input = input("\nYOU (caller): ")
        if user_input.lower() == "quit":
            break

        history.append({"role": "user", "content": user_input})
        result = get_agent_reply(history)

        print(f"\nAGENT: {result['reply']}")
        print(f"  [classification: {result['classification']} | reasoning: {result['reasoning']} | action: {result['action_needed']} | lang: {result['detected_language']}]")

        history.append({"role": "assistant", "content": result["reply"]})

        audio_path = speak(result["reply"], f"turn_{turn}.mp3")
        print(f"  [audio saved: {audio_path}]")

        if result["action_needed"] == "send_whatsapp":
            print("  >>> WOULD FIRE WHATSAPP HERE (Day 4 builds this for real)")
        elif result["action_needed"] == "schedule_callback":
            print("  >>> WOULD BOOK CALLBACK HERE (Day 4 builds this for real)")


if __name__ == "__main__":
    main()
