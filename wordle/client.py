# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Wordle Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import WordleAction, WordleObservation


class WordleEnv(
    EnvClient[WordleAction, WordleObservation, State]
):
    """
    Client for the Wordle Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with WordleEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.word_hints_llm)
        ...
        ...     result = client.step(WordleAction(word_guess="crane"))
        ...     print(result.observation.word_hints)      # e.g. [0, 1, 2, 0, 0]
        ...     print(result.observation.word_hints_llm)  # human-readable hint string

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = WordleEnv.from_docker_image("wordle-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(WordleAction(word_guess="crane"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: WordleAction) -> Dict:
        """
        Convert WordleAction to JSON payload for step message.

        Args:
            action: WordleAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "word_guess": action.word_guess,
        }

    def _parse_result(self, payload: Dict) -> StepResult[WordleObservation]:
        """
        Parse server response into StepResult[WordleObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with WordleObservation
        """
        obs_data = payload.get("observation", {})
        observation = WordleObservation(
            word_hints_llm=obs_data.get("word_hints_llm", ""),
            word_hints=obs_data.get("word_hints", [0, 0, 0, 0, 0]),
            guessed_word=obs_data.get("guessed_word", ""),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
