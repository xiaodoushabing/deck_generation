"""
Slide Content Generation Module

This module handles the generation of detailed slide content based on
slide structures and reference markdown content.
"""

from typing import Any, Tuple

from utilities import FileIO

from .llm_utils import LLMUtils


class SlideContentGenerator:
    """Handles slide content generation for presentations."""

    def __init__(self, client):
        """
        Initialize the content generator.

        Args:
            client: OpenAI client instance for API calls
        """
        self.client = client

    @property
    def output_format(self) -> str:
        """
        Get the output format for slide content generation.

        Returns:
            Formatted output string
        """
        return """
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

    @property
    def system_prompt(self) -> str:
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

    @staticmethod
    def _get_user_prompt(slide_structure: str, markdown_content: str) -> str:
        """
        Generate user prompt for content generation.

        Args:
            slide_structure: JSON structure of slides
            markdown_content: Reference markdown content

        Returns:
            Formatted user prompt string
        """
        return f"""
Use the provided slide structure as your guide and extract relevant key information from the reference content to create detailed slides.

**Slide Structure to Follow:**
{slide_structure}

**Reference Content:**
```markdown
{markdown_content}
```

**Instructions:**
1. Follow the exact slide structure provided - create slides with the specified headings and key messages
2. For each slide, extract and synthesize relevant information from the reference content that supports the slide's key message
3. If reference content is limited or unavailable for a specific slide, use your knowledge to provide relevant content that aligns with the slide's purpose.
For such content, ensure it is accurate and contextually appropriate.
Also, clearly indicate when you are using your own knowledge versus the reference content.
4. Maintain logical flow between slides as outlined in the structure
5. Ensure each slide has substantive content - avoid placeholder text unless absolutely necessary.
6. Include speaker notes where appropriate to provide additional context

Generate the complete presentation in markdown format, ready for Pandoc conversion to PowerPoint.
"""

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
        system_prompt = self.system_prompt
        user_prompt_formatted = self._get_user_prompt(slide_structure, markdown_content)

        # Get response from LLM
        content_response, usage = LLMUtils.get_response(
            self.client, system_prompt, user_prompt_formatted, context="Content generation"
        )

        return content_response, usage
