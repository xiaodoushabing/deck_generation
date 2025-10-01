"""
Slide Structure Generation Module

This module handles the generation of presentation slide structures (outlines)
based on user prompts and reference markdown content.
"""

from typing import Any, Tuple

from utilities import FileIO

from .llm_utils import LLMUtils


class SlideStructureGenerator:
    """Handles slide structure generation for presentations."""

    def __init__(self, client):
        """
        Initialize the structure generator.

        Args:
            client: OpenAI client instance for API calls
        """
        self.client = client

    @property
    def output_format(self) -> str:
        """
        Get the output format for slide structure generation.

        Returns:
            Formatted output string
        """
        return (
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

    @property
    def system_prompt(self) -> str:
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

    @staticmethod
    def _get_user_prompt(user_prompt: str, markdown_content: str, num_slides: int) -> str:
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
        system_prompt = self.system_prompt
        user_prompt_formatted = self._get_user_prompt(user_prompt, markdown_content, num_slides)

        # Get response from LLM
        structure_response, usage = LLMUtils.get_response(
            self.client, system_prompt, user_prompt_formatted, context="Structure generation"
        )

        return structure_response, usage
