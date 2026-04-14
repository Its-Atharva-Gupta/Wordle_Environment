"""
Wordle debug client — starts the uvicorn server in a background thread,
then loops asking for word guesses and printing the full WordleObservation.
"""
import asyncio
import threading
import uvicorn

from wordle.client import WordleEnv
from wordle.models import WordleAction


SERVER_URL = "http://localhost:8000"


def start_server():
    from wordle.server.app import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


async def main():
    # Start uvicorn in a daemon thread so it dies when the script exits
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Give the server a moment to bind
    await asyncio.sleep(1.5)

    async with WordleEnv(base_url=SERVER_URL) as env:
        result = await env.reset()
        obs = result.observation
        print("\n=== Wordle Debug Client ===")
        print(f"word_hints_llm : {obs.word_hints_llm}")
        print(f"word_hints     : {obs.word_hints}")
        print(f"guessed_word   : {obs.guessed_word!r}")
        print(f"done           : {obs.done}")
        print(f"reward         : {obs.reward}")
        print(f"metadata       : {obs.metadata}")
        print()

        loop = asyncio.get_event_loop()
        while True:
            try:
                guess = await loop.run_in_executor(
                    None, lambda: input("Enter guess (5-letter word): ").strip()
                )
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            result = await env.step(WordleAction(word_guess=guess))
            obs = result.observation

            print()
            print(f"word_hints_llm : {obs.word_hints_llm}")
            print(f"word_hints     : {obs.word_hints}")
            print(f"guessed_word   : {obs.guessed_word!r}")
            print(f"done           : {obs.done}")
            print(f"reward         : {obs.reward}")
            print(f"metadata       : {obs.metadata}")
            print()

            if obs.done:
                if obs.word_hints == [2, 2, 2, 2, 2]:
                    print(f"You won! The word was: {obs.guessed_word.upper()}")
                else:
                    # The correct word is included in word_hints_llm on game-over
                    print(f"You lost. {obs.word_hints_llm}")
                print("Restart the script to play again.")
                break


if __name__ == "__main__":
    asyncio.run(main())
