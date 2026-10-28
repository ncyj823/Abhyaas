"""CLI text chat for testing conversations with Abhyaas personas."""

import argparse
import sys
from typing import Any, Dict

from app.customer import process_turn
from app.llm import chat_json
from app.personas import get_persona_by_id, load_personas
from app.sessions import Session, create_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Abhyaas CLI – practice a sales call")
    parser.add_argument("--persona", type=str, help="Persona ID to use")
    parser.add_argument("--debug", action="store_true", help="Show revealed facts after each turn")
    args = parser.parse_args()

    personas = load_personas()
    if not personas:
        print("No personas found. Check app/data/personas/ directory.")
        sys.exit(1)

    # Pick persona
    if args.persona:
        try:
            persona = get_persona_by_id(args.persona)
        except KeyError:
            print(f"Persona '{args.persona}' not found.")
            print(f"Available: {', '.join(p.id for p in personas)}")
            sys.exit(1)
    else:
        print("Available personas:")
        for i, p in enumerate(personas, 1):
            print(f"  {i}. {p.id} — {p.name} ({p.business}) [{p.language_style}]")
        choice = input("\nPick a number: ").strip()
        try:
            persona = personas[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice.")
            sys.exit(1)

    # Create session
    session = create_session(persona)
    print(f"\n{'='*60}")
    print(f"  Call with: {persona.name} ({persona.business})")
    print(f"  Style: {persona.language_style}")
    print(f"{'='*60}")
    print(f"\n  Customer: {persona.opening_line}\n")

    # Add opening line as assistant message
    session.add_assistant_message(persona.opening_line)

    # Conversation loop
    while True:
        try:
            rep_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nCall ended.")
            break

        if not rep_input:
            continue

        if rep_input.lower() in ("quit", "exit", "end", "bye"):
            print("\nCall ended. What's your read on this customer?")
            guess = input("  HOT / WARM / COLD: ").strip().upper()
            if guess not in ("HOT", "WARM", "COLD"):
                print("  Invalid guess, defaulting to WARM")
                guess = "WARM"

            print(f"\n  True intent was: {persona.true_intent}")
            print(f"  Your guess: {guess}")
            print(f"  Discovery: {len(session.revealed_facts)}/{session.total_facts} facts revealed")
            print(f"  Facts found: {sorted(session.revealed_facts) if session.revealed_facts else 'none'}")
            break

        session.add_user_message(rep_input)

        try:
            reply, newly_revealed = process_turn(
                persona=persona,
                conversation=session.conversation,
                revealed_so_far=session.revealed_facts,
                llm_chat_json=chat_json,
            )
        except Exception as e:
            print(f"\n  [Error: {e}. Try again.]\n")
            # Remove the failed user message
            session.conversation.pop()
            continue

        session.mark_revealed(newly_revealed)
        session.add_assistant_message(reply)

        print(f"\n  Customer: {reply}\n")

        if args.debug and newly_revealed:
            print(f"  [DEBUG] Newly revealed: {sorted(newly_revealed)}")
            print(f"  [DEBUG] All revealed: {sorted(session.revealed_facts)}")
            print()


if __name__ == "__main__":
    main()
