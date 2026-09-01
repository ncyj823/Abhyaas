"""
Day 3 test: same as test_pipeline_voice.py, but now routed through the
LangGraph state machine (app/graph.py) instead of calling brain.py directly.

Functionally identical output to Day 2 - the point of this test is to
confirm the graph restructuring didn't break anything, before Day 4 swaps
the placeholder action nodes for real WhatsApp/scheduler tool calls.

Run: python test_pipeline_graph.py
"""

from app.graph import run_turn
from app.voice_out import speak
from app.voice_in import record_audio, transcribe_audio

def main():
    print("=== Saarthi graph test (Day 3) ===")
    print("Press Enter to start a 5-second recording each turn. Say 'quit' to exit.\n")

    history = [{"role": "user", "content": "[CALL CONNECTED - greet the customer and introduce yourself]"}]
    turn = 0

    state = run_turn(history)
    print(f"AGENT: {state['reply']}")
    print(f"  [classification: {state['classification']} | action: {state['action_needed']} | action_taken: {state['action_taken']}]")
    speak(state["reply"], f"turn_{turn}.wav")
    history = state["history"]

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

        history = history + [{"role": "user", "content": user_text}]
        state = run_turn(history)

        print(f"\nAGENT: {state['reply']}")
        print(f"  [classification: {state['classification']} | reasoning: {state['reasoning']} | action: {state['action_needed']} | action_taken: {state['action_taken']} | lang: {state['detected_language']}]")

        history = state["history"]
        speak(state["reply"], f"turn_{turn}.wav")


if __name__ == "__main__":
    main()
