# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Wordle Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""
from pathlib import Path
from random import randint
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import WordleAction, WordleObservation
except ImportError:
    from models import WordleAction, WordleObservation


class WordleEnvironment(Environment):
    """
    A simple echo environment that echoes back messages.

    This environment is designed for testing the HTTP server infrastructure.
    It maintains minimal state and simply echoes back whatever message it receives.

    Example:
        >>> env = WordleEnvironment()
        >>> obs = env.reset()
        >>> print(obs.echoed_message)  # "Wordle environment ready!"
        >>>
        >>> obs = env.step(WordleAction(message="Hello"))
        >>> print(obs.echoed_message)  # "Hello"
        >>> print(obs.message_length)  # 5
    """

    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the wordle environment."""
        self._guesses_allowed = 10
        self._current_guess_count = 0
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0
        self.current_word: str | None = None
        data_path = Path(__file__).parent /"data" /"data.txt"
        with open(data_path, "r") as file:
            self.lines = file.readlines()

        self.lines = [line.strip() for line in self.lines if line.strip()]

    def reset(self) -> WordleObservation:
        """
        Reset the environment.

        Returns:
            WordleObservation with a ready message
        """
        self._current_guess_count = 0
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count += 1
        self.current_word = self.lines[randint(0, len(self.lines) - 1)]
        return WordleObservation(
            word_hints_llm="Wordle environment ready!",
            word_hints=[0, 0, 0, 0, 0],
            guessed_word="",
        )

    def _compute_hints(self, word: str) -> tuple[list[int], list[str]]:
        """
        Compute Wordle hints using a two-pass algorithm to correctly handle
        duplicate letters.

        Pass 1: mark greens and track unmatched target letters.
        Pass 2: assign yellows only against unmatched target letters.
        """
        hints = [0] * 5
        hint_messages = [""] * 5
        # Track which target letters are still unmatched after green pass
        unmatched = list(self.current_word)

        # Pass 1: greens
        for i in range(5):
            if word[i] == self.current_word[i]:
                hints[i] = 2
                hint_messages[i] = f"Letter '{word[i]}' is correct and in the right position (green)."
                unmatched[i] = ""  # consumed

        # Pass 2: yellows and greys
        for i in range(5):
            if hints[i] == 2:
                continue
            if word[i] in unmatched:
                hints[i] = 1
                hint_messages[i] = f"Letter '{word[i]}' is in the word but in the wrong position (yellow)."
                unmatched[unmatched.index(word[i])] = ""  # consume one occurrence
            else:
                hints[i] = 0
                hint_messages[i] = f"Letter '{word[i]}' is not in the word (grey)."

        return hints, hint_messages

    def step(self, action: WordleAction) -> WordleObservation:  # type: ignore[override]
        """
        Execute a step in the environment.

        Args:
            action: WordleAction containing the word guess

        Returns:
            WordleObservation with hints and reward
        """
        if self.current_word is None:
            raise RuntimeError("reset() must be called before step()")

        word = action.word_guess.strip().lower()
        self._state.step_count += 1

        # Validate length before consuming a turn
        if len(word) != 5:
            return WordleObservation(
                word_hints_llm="Invalid guess. Please enter a 5-letter word.",
                word_hints=[0, 0, 0, 0, 0],
                guessed_word=word,
                done=False,
                reward=-1,
                metadata={"original_message": word, "step": self._state.step_count},
            )

        self._current_guess_count += 1

        if word == self.current_word:
            return WordleObservation(
                word_hints_llm="Correct! All letters are green. Word correctly guessed.",
                word_hints=[2, 2, 2, 2, 2],
                guessed_word=word,
                done=True,
                reward=10,
                metadata={"original_message": word, "step": self._state.step_count},
            )

        hints, hint_messages = self._compute_hints(word)

        if self._current_guess_count >= self._guesses_allowed:
            llm_hints = (
                f"Game over! You've used all {self._guesses_allowed} guesses. "
                f"The correct word was '{self.current_word}'. "
                f"Final guess hints: {hint_messages}"
            )
            return WordleObservation(
                word_hints_llm=llm_hints,
                word_hints=hints,
                guessed_word=word,
                done=True,
                reward=-10,
                metadata={"original_message": word, "step": self._state.step_count},
            )

        llm_hints = f"Guess '{word}' received. Hints: {hint_messages}. Try again!"
        return WordleObservation(
            word_hints_llm=llm_hints,
            word_hints=hints,
            guessed_word=word,
            done=False,
            reward=-0.5,
            metadata={"original_message": word, "step": self._state.step_count},
        )
        


    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
