"""
Interactive Gemini chat in the terminal (multi-turn).

Setup:
  pip install google-generativeai
  set GEMINI_API_KEY=your_key   # Windows PowerShell: $env:GEMINI_API_KEY="..."

Run:
  python scripts/gemini_chat.py

Type your message and press Enter. Commands: quit, exit, clear (reset history).
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    try:
        import google.generativeai as genai
    except ImportError:
        print("Missing package. Install with: pip install google-generativeai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Set GEMINI_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    chat = model.start_chat(history=[])

    print(f"Gemini chat ({model_name}). Commands: quit | exit | clear\n")

    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        low = line.lower()
        if low in ("quit", "exit", "q"):
            break
        if low == "clear":
            chat = model.start_chat(history=[])
            print("(History cleared.)\n")
            continue

        try:
            response = chat.send_message(line)
            text = getattr(response, "text", None) or ""
            print(f"Gemini: {text}\n")
        except Exception as e:
            print(f"Error: {e}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
