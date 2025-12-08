"""
Google Gemini API client for AI chat.

Uses OpenAI-compatible endpoint for simplified integration.
"""

from django.conf import settings
from openai import OpenAI


def send_to_gemini(
    system_context: str, messages: list[dict], model: str = "gemini-2.5-flash"
) -> tuple[str, int, int]:
    """
    Send a conversation to Gemini and get a response.

    Args:
        system_context: The system prompt with matter context
        messages: List of {"role": "user"|"assistant", "content": str}
        model: Gemini model to use (gemini-2.5-flash or gemini-2.5-pro)

    Returns:
        tuple of (response_text, input_tokens, output_tokens)

    Raises:
        openai.APIError: If the API call fails
    """
    client = OpenAI(
        api_key=settings.GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    # Format messages with system context first
    formatted_messages = [{"role": "system", "content": system_context}]
    formatted_messages.extend(
        {"role": msg["role"], "content": msg["content"]} for msg in messages
    )

    response = client.chat.completions.create(
        model=model,
        messages=formatted_messages,
    )

    response_text = response.choices[0].message.content
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    return response_text, input_tokens, output_tokens
