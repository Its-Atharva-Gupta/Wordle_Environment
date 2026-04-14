# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Wordle Environment.

The wordle environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class WordleAction(Action):
    """Action for the Wordle environment - just a message to echo."""

    word_guess: str = Field(..., description="The word guessed by the agent")

class WordleObservation(Observation):
    """Observation from the Wordle environment - the echoed message."""

    word_hints_llm: str = Field(..., description="Hints for the guessed word")
    word_hints: list[int] = Field(..., description="Hints for the guessed word in list form. 0 for grey, 1 for yellow, 2 for green  ")
    guessed_word: str = Field(..., description="The word guessed by the agent")