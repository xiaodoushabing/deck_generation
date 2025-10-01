"""
Slide Content Generation Module

This module handles the generation of detailed slide content based on
slide structures and reference markdown content.
"""

from typing import Any, Tuple

from utilities import FileIO


class SlideContentGenerator:
    """Handles slide content generation for presentations."""

    def __init__(self, client):
        """
        Initialize the content generator.

        Args:
            client: OpenAI client instance for API calls
        """
        self.client = client
        self.output_format = """
The output must be a markdown document structured for Pandoc conversion to PowerPoint.
Follow these formatting rules:

- Use the guidelines from Pandoc's manual: https://pandoc.org/MANUAL.html
- Use `#` for the Presentation Title (this maps to the **Title Slide** layout).
- Use `##` for each new slide title (this maps to the **Title and Content** layout unless otherwise specified).
- Use `---` to separate slides. Ensure newline above and below this.
Include speaker notes using the following syntax:
::: notes
This is my note.
- It can contain Markdown
- like this list
:::

- To add tables, use standard markdown syntax for tables. Example:
| Header 1 | Header 2 | Header 3 ...|
| --- | --- | --- |
| Content 1 | Content 2 | Content 3 |
| ... | ... | ... |

- Use fenced code blocks. These begin with a row of three or more backticks (`) and end with a row of backticks that must be at least as long as the starting row. Everything between these lines is treated as code. No indentation is necessary:

``````{#mycode .haskell .numberLines startFrom="100"}
if (a > 3) {
    moveShip(5 * gravity, DOWN);
}
``````

Like regular code blocks, fenced code blocks must be separated from surrounding text by blank lines.
If the code itself contains a row of tildes or backticks, just use a longer row of tildes or backticks at the start and end:

`````````````````
``````
code including tildes
``````
`````````````````

In the above code block example, mycode is an identifier, haskell and numberLines are classes, and startFrom is an attribute with value 100.
Powerpoint can use this information to do syntax highlighting.

- For slides with text followed by images or tables, Pandoc will use the **Content with Caption** layout.
- For slides with only speaker notes or blank content, Pandoc will use the **Blank** layout.
- Footnotes are supported:
    Regular: Here is a footnote reference,
    Inline: Inline note.^[This is an inline footnote.]
"""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for slide content generation."""
        return f"""
You are an expert at creating concise, visual slide content.

Task: Generate detailed slide content using the provided structure and reference material.

Content Guidelines:
- Maximum 5 bullet points per slide, each conveying a key idea
- Use tables for comparisons of multiple items
- Focus on key information, avoid dense text
- Extract relevant sections from reference material
- Ensure visual, scannable format

Output format:
{self.output_format}
"""

    def _get_user_prompt(self, slide_structure: str, markdown_content: str) -> str:
        """
        Generate user prompt for content generation.

        Args:
            slide_structure: JSON structure of slides
            markdown_content: Reference markdown content

        Returns:
            Formatted user prompt string
        """
        return f"""
Slide structure:
{slide_structure}.

Reference markdown content:
```markdown
{markdown_content}
```
Please generate a presentation in markdown format described above.
The markdown should be clean and ready for conversion into a PowerPoint presentation using Pandoc.
"""

    def _get_response(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 10000, model: str = "gpt-oss-120b"
    ) -> Tuple[str, Any]:
        """
        Get LLM response for content generation.

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

        print(f"Content generation response:\n{llm_response}")
        print(f"Prompt tokens used: {llm_usage.prompt_tokens}")
        print(f"Completion tokens used: {llm_usage.completion_tokens}")
        print(f"Total tokens used: {llm_usage.total_tokens}")

        return llm_response, llm_usage

    def generate_content(self, slide_structure: str, markdown_path: str = None) -> Tuple[str, Any]:
        """
        Generate slide content based on structure and optional markdown reference.

        Args:
            slide_structure: JSON structure of slides
            markdown_path: Path to reference markdown file (optional)

        Returns:
            Tuple of (content_response, usage_info)
        """
        # Load markdown content if path provided
        if markdown_path:
            markdown_content = FileIO.fread(markdown_path)
        else:
            markdown_content = ""

        # Generate prompts
        system_prompt = self._get_system_prompt()
        user_prompt_formatted = self._get_user_prompt(slide_structure, markdown_content)

        # Get response from LLM
        content_response, usage = self._get_response(system_prompt, user_prompt_formatted)

        return content_response, usage
