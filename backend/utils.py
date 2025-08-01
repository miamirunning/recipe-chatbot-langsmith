from __future__ import annotations

"""Utility helpers for the recipe chatbot backend.

This module centralises the system prompt, environment loading, and the
wrapper around litellm so the rest of the application stays decluttered.
"""

import os
from typing import Final, List, Dict, Any

import litellm  # type: ignore
from dotenv import load_dotenv
from langsmith import traceable

# Ensure the .env file is loaded as early as possible.
load_dotenv(override=False)

# --- Constants -------------------------------------------------------------------

SYSTEM_PROMPT: Final[str] = (
    "You are an expert chef recommending delicious and useful recipes. "
    "Present only one recipe at a time. If the user doesn't specify what ingredients "
    "they have available, assume only basic ingredients are available. "
    "Be descriptive in the steps of the recipe, so it is easy to follow. "
    "Have variety in your recipes, don't just recommend the same thing over and over. "
    "You MUST suggest a complete recipe; don't ask follow-up questions. "
    "Mention the serving size in the recipe. If not specified, assume 2 people. "
    
    "### Role "
    "You are acting as a private chef who advises clients on what they can make for themselves. "

"###Instructions "

"Your answer will be a clear recipe with a one sentence summary at the top; facts as bullet points: number of people, required prep time, type of meal, confirm dietary restriction; the ingredient list, the kitchen tool list, step by step instructions for how to prepare for chef at the kitchen proficiency shown in the context. "

"### Context "

"The following are options that the user can specify. The default answer is included after the colon, use those if that criteria is not otherwise specified "
"* allergies: no allergies "
"* dietary preferences: standard American diet "
"* kitchen proficiency: medium level of skills "
"* available kitchen appliances and tools: all standard appliances found in an American kitchen, but no gourmet tools "
"* Type of meal: lunch "
"* Number of people the meal serves: 2 "
"* Season: summer "
"* What are they in the mood for?: quick low fuss but nutritious meal "


)

# Fetch configuration *after* we loaded the .env file.
MODEL_NAME: Final[str] = os.environ.get("MODEL_NAME", "gpt-4o-mini")


# --- Agent wrapper ---------------------------------------------------------------

@traceable(name="LiteLLM", run_type="llm")
def litellm_completion(model: str, messages: List[Dict[str, str]], **kwargs: Any):
    completion = litellm.completion(
        model=model,
        messages=messages,
        **kwargs,
    )
    return completion

def get_agent_response(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:  # noqa: WPS231
    """Call the underlying large-language model via *litellm*.

    Parameters
    ----------
    messages:
        The full conversation history. Each item is a dict with "role" and "content".

    Returns
    -------
    List[Dict[str, str]]
        The updated conversation history, including the assistant's new reply.
    """

    # litellm is model-agnostic; we only need to supply the model name and key.
    # The first message is assumed to be the system prompt if not explicitly provided
    # or if the history is empty. We'll ensure the system prompt is always first.
    current_messages: List[Dict[str, str]]
    if not messages or messages[0]["role"] != "system":
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    else:
        current_messages = messages

    completion = litellm_completion(
        model=MODEL_NAME,
        messages=current_messages, # Pass the full history
    )

    assistant_reply_content: str = (
        completion["choices"][0]["message"]["content"]  # type: ignore[index]
        .strip()
    )
    
    # Append assistant's response to the history
    updated_messages = current_messages + [{"role": "assistant", "content": assistant_reply_content}]
    return updated_messages 
