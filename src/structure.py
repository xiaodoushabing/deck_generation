"""
Slide Structure Generation Module

This module handles the generation of presentation slide structures (outlines)
based on user prompts and reference markdown content.
"""

from typing import Any, Tuple

from utilities import FileIO


class SlideStructureGenerator:
    """Handles slide structure generation for presentations."""

    def __init__(self, client):
        """
        Initialize the structure generator.

        Args:
            client: OpenAI client instance for API calls
        """
        self.client = client
        self.output_format = (
            "Return only the JSON object with the following sample structure:\n"
            "{\n"
            '  "title": "Title of the presentation",\n'
            '  "slides": [\n'
            "    {\n"
            '      "heading": "Slide title",\n'
            '      "key_message": "Key message of the slide"\n'
            "    },\n"
            "    ...\n"
            "  ]\n"
            "}\n"
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for slide structure generation."""
        return f"""
You are an expert presentation designer creating logical slide outlines.

Task: Generate a coherent slide structure (titles only, no content) based on the user prompt and reference document.

Requirements:
- Always include Introduction and Summary slides
- Extract key sections from the markdown content
- Ensure logical flow and alignment with user prompt
- Output only slide titles in JSON format

Output format:
{self.output_format}
"""

    def _get_user_prompt(self, user_prompt: str, markdown_content: str, num_slides: int) -> str:
        """
        Generate user prompt for structure generation.

        Args:
            user_prompt: User's presentation request
            markdown_content: Reference markdown content
            num_slides: Number of slides to generate

        Returns:
            Formatted user prompt string
        """
        return f"""
{user_prompt}.

Reference markdown content:
```markdown
{markdown_content}
```

Only generate {num_slides} slides.
Please generate the slide outline in the JSON format described above.
"""

    def _get_response(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 10000, model: str = "gpt-oss-120b"
    ) -> Tuple[str, Any]:
        """
        Get LLM response for structure generation.

        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            max_tokens: Maximum tokens for response
            model: Model to use for generation

        Returns:
            Tuple of (response_content, usage_info)
        """
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, stream=False)

        message = response.choices[0].message
        llm_response = message.content
        llm_usage = response.usage

        print(f"Structure generation response:\n{llm_response}")
        print(f"Prompt tokens used: {llm_usage.prompt_tokens}")
        print(f"Completion tokens used: {llm_usage.completion_tokens}")
        print(f"Total tokens used: {llm_usage.total_tokens}")

        return llm_response, llm_usage

    def generate_structure(self, user_prompt: str, markdown_path: str = None, num_slides: int = 20) -> Tuple[str, Any]:
        """
        Generate slide structure based on user prompt and optional markdown reference.

        Args:
            user_prompt: User's presentation request
            markdown_path: Path to reference markdown file (optional)
            num_slides: Number of slides to generate

        Returns:
            Tuple of (structure_response, usage_info)
        """
        # Load markdown content if path provided
        if markdown_path:
            markdown_content = FileIO.fread(markdown_path)
        else:
            markdown_content = ""

        # Generate prompts
        system_prompt = self._get_system_prompt()
        user_prompt_formatted = self._get_user_prompt(user_prompt, markdown_content, num_slides)

        # Get response from LLM
        structure_response, usage = self._get_response(system_prompt, user_prompt_formatted)

        return structure_response, usage
