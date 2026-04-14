"""
Groq-powered Wordle agent — plays one episode against the Wordle environment.
"""
import asyncio
import os
import re
import threading
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from groq import Groq

from wordle.client import WordleEnv
from wordle.models import WordleAction

load_dotenv(Path(__file__).parent / ".env")

SERVER_URL = "http://localhost:8000"
MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are playing Wordle. Rules:
- The secret word is 5 letters long.
- Each guess must be a real 5-letter English word.
- After each guess you receive per-letter hints:
    2 (green)  = correct letter, correct position
    1 (yellow) = correct letter, wrong position
    0 (grey)   = letter not in the word

Strategy: use the hints to eliminate possibilities. Avoid reusing grey letters.
Respond with ONLY the 5-letter word guess, nothing else."""


def build_user_message(history: list[dict]) -> str:
    if not history:
        return "Start the game. Give your first guess."
    lines = ["Here are your guesses so far:"]
    for i, entry in enumerate(history, 1):
        lines.append(f"  Guess {i} ('{entry['word']}'): {entry['hint_text']}")
    lines.append("Give your next guess.")
    return "\n".join(lines)


def llm_guess(history: list[dict]) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(history)},
        ],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    # Extract first 5-letter alphabetic token from the response
    match = re.search(r"\b([a-zA-Z]{5})\b", raw)
    return match.group(1).lower() if match else raw.lower()[:5]


def start_server():
    from wordle.server.app import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


async def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    await asyncio.sleep(1.5)

    history = []  # list of {"word": str, "hints": list[int]}

    async with WordleEnv(base_url=SERVER_URL) as env:
        await env.reset()
        print("=== Groq Wordle Agent ===\n")

        while True:
            guess = llm_guess(history)
            print(f"Agent guesses: {guess.upper()}")

            result = await env.step(WordleAction(word_guess=guess))
            obs = result.observation

            print(f"  hints     : {obs.word_hints}")
            print(f"  llm_hints : {obs.word_hints_llm}")
            print()

            history.append({"word": guess, "hint_text": obs.word_hints_llm})

            if obs.done:
                if obs.word_hints == [2, 2, 2, 2, 2]:
                    print(f"Agent won in {len(history)} guess(es)! Word: {guess.upper()}")
                else:
                    print(f"Agent lost. {obs.word_hints_llm}")
                break


if __name__ == "__main__":
    asyncio.run(main())
