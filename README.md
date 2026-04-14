# Wordle AI Agent

A Wordle game environment with two modes of play: an interactive debug client for manual play and a Groq-powered LLM agent that plays autonomously. Built on the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework.

## Overview

The project spins up a local FastAPI/WebSocket server that runs the Wordle game logic, then connects to it via one of two clients:

- **`main.py`** — interactive debug client; you type guesses in the terminal
- **`inference.py`** — autonomous agent powered by Groq's `llama-3.3-70b-versatile` model

Both clients start the server automatically in a background thread, so no separate server process is needed.

## Project Structure

```
chess/
├── main.py               # Interactive debug client
├── inference.py          # Groq LLM agent
├── pyproject.toml        # Top-level project metadata & dependencies
├── uv.lock               # Locked dependency tree
└── wordle/               # OpenEnv Wordle environment package
    ├── __init__.py
    ├── client.py         # WordleEnv client (WebSocket-based)
    ├── models.py         # WordleAction / WordleObservation types
    ├── openenv.yaml      # OpenEnv manifest (for HF Spaces deploy)
    ├── pyproject.toml    # Environment package metadata
    ├── README.md         # Environment-specific docs
    └── server/
        ├── app.py                  # FastAPI app (HTTP + WebSocket endpoints)
        ├── wordle_environment.py   # Core game logic
        ├── Dockerfile              # Container image definition
        └── data/
            └── data.txt            # Word list
```

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A [Groq API key](https://console.groq.com/) (only required for `inference.py`)

## Installation

```bash
# Clone / navigate into the project directory
cd chess

# Install dependencies with uv (reads uv.lock for reproducible installs)
uv sync

# Or with pip
pip install -e .
```

## Configuration

For the LLM agent, create a `.env` file in the `chess/` directory:

```
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

### Interactive Play (`main.py`)

Starts the server and drops you into a prompt where you type 5-letter guesses:

```bash
uv run main.py
# or
python main.py
```

Example session:

```
=== Wordle Debug Client ===
word_hints_llm : Wordle environment ready!
word_hints     : [0, 0, 0, 0, 0]
guessed_word   : ''
done           : False
reward         : None

Enter guess (5-letter word): crane
word_hints_llm : Guess 'crane' received. Hints: [...]
word_hints     : [0, 1, 2, 0, 0]
...
```

Hint values:
| Value | Colour | Meaning |
|-------|--------|---------|
| `0`   | Grey   | Letter not in the word |
| `1`   | Yellow | Correct letter, wrong position |
| `2`   | Green  | Correct letter, correct position |

Win condition: all five hints are `2` (`[2, 2, 2, 2, 2]`).
You have **10 guesses** per game. Restart the script to play again.

### LLM Agent (`inference.py`)

Starts the server and lets the Groq model play a full game autonomously:

```bash
uv run inference.py
# or
python inference.py
```

Example output:

```
=== Groq Wordle Agent ===

Agent guesses: CRANE
  hints     : [0, 1, 2, 0, 0]
  llm_hints : Guess 'crane' received. Hints: [...]

Agent guesses: BLAST
  hints     : [2, 2, 2, 2, 2]
  llm_hints : Correct! All letters are green. Word correctly guessed.

Agent won in 2 guess(es)! Word: BLAST
```

The agent uses a rolling conversation history so each new guess is informed by all previous hint messages.

## Game Rules

- The secret word is exactly **5 letters** long.
- Guesses shorter or longer than 5 letters are rejected (no turn consumed).
- You have **10 attempts** to guess the word.
- **Rewards**: `+10` for a correct guess, `-0.5` per incorrect guess, `-10` on game over, `-1` for an invalid guess.

## Environment API

The underlying environment exposes HTTP and WebSocket endpoints at `http://localhost:8000`:

| Endpoint       | Method    | Description                          |
|----------------|-----------|--------------------------------------|
| `/reset`       | POST      | Start a new episode                  |
| `/step`        | POST      | Submit a guess                       |
| `/state`       | GET       | Get current episode state            |
| `/schema`      | GET       | Action / observation JSON schemas    |
| `/ws`          | WebSocket | Persistent low-latency session       |
| `/health`      | GET       | Health check                         |
| `/web`         | GET       | Interactive web UI (Docker/HF only)  |
| `/docs`        | GET       | OpenAPI / Swagger docs               |

### Action

```python
WordleAction(word_guess: str)  # 5-letter word
```

### Observation

```python
WordleObservation(
    word_hints_llm: str,     # Human-readable hint string
    word_hints: list[int],   # Per-letter hints: 0=grey, 1=yellow, 2=green
    guessed_word: str,       # The word that was guessed
    done: bool,              # True when game ends (win or loss)
    reward: float | None,    # Numeric reward signal
    metadata: dict,          # Step count and original guess
)
```

## Running the Server Standalone

```bash
# Via uv (from the wordle/ directory)
uv run --project wordle server

# Via uvicorn directly
uvicorn wordle.server.app:app --reload --host 0.0.0.0 --port 8000

# Via Docker
docker build -t wordle-env:latest -f wordle/server/Dockerfile wordle/
docker run -p 8000:8000 wordle-env:latest
```

## Deploying to Hugging Face Spaces

```bash
cd wordle
openenv push                          # deploy to your namespace
openenv push --repo-id my-org/wordle  # deploy to a specific repo
openenv push --private                # deploy as private
```

See [`wordle/README.md`](wordle/README.md) for full deployment options.

## Dependencies

| Package | Purpose |
|---------|---------|
| `openenv-core` | OpenEnv client/server framework |
| `groq` | Groq SDK for LLM inference |
| `python-dotenv` | `.env` file loading |
| `pygame` | (available for future GUI work) |
| `uvicorn` | ASGI server (transitive via openenv-core) |
