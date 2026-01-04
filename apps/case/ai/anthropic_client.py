"""
Anthropic Claude API client for AI chat.
"""

import anthropic
from django.conf import settings


def send_to_claude(
    system_context: str,
    messages: list[dict],
    model: str = "claude-sonnet-4-20250514",
) -> tuple[str, int, int]:
    """
    Send a conversation to Claude and get a response.

    Args:
        system_context: The system prompt with matter context
        messages: List of {"role": "user"|"assistant", "content": str}
        model: Claude model to use (claude-sonnet-4-20250514 or claude-opus-4-5-20251101)

    Returns:
        tuple of (response_text, input_tokens, output_tokens)

    Raises:
        anthropic.APIError: If the API call fails
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Format messages for Anthropic API
    formatted_messages = [
        {"role": msg["role"], "content": msg["content"]} for msg in messages
    ]

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_context,
        messages=formatted_messages,
    )

    response_text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    return response_text, input_tokens, output_tokens
