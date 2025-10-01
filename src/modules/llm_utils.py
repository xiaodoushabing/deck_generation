"""
LLM Utility Functions

Shared utilities for interacting with Language Models across different modules.
"""

from typing import Any, Tuple


class LLMUtils:
    """Utility class for LLM interactions."""

    @staticmethod
    def get_response(
        client,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 10000,
        model: str = "gpt-oss-120b",
        context: str = "Processing",
    ) -> Tuple[str, Any]:
        """
        Get LLM response for any processing task.

        Args:
            client: OpenAI client instance
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            max_tokens: Maximum tokens for response
            model: Model to use for generation
            context: Context description for logging

        Returns:
            Tuple of (response_content, usage_info)
        """
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, stream=False)

        message = response.choices[0].message
        llm_response = message.content
        llm_usage = response.usage

        print(f"{context} response:\n{llm_response}")
        print(f"Prompt tokens used: {llm_usage.prompt_tokens}")
        print(f"Completion tokens used: {llm_usage.completion_tokens}")
        print(f"Total tokens used: {llm_usage.total_tokens}")

        return llm_response, llm_usage
