"""
Mermaid Diagram Generation and Validation Module

This module handles the generation, cleanup, and validation of mermaid diagrams
for PowerPoint presentations.
"""

import re
from typing import Any, Tuple


class MermaidProcessor:
    """Handles mermaid diagram generation, cleanup, and validation."""

    def __init__(self, client):
        """
        Initialize the mermaid processor.

        Args:
            client: OpenAI client instance for API calls
        """
        self.client = client
        self.few_shot_examples = """
- Sequence diagram:

```mermaid
sequenceDiagram
    Alice->>John: Hello John, how are you?
    John-->>Alice: Great!
    Alice-)John: See you later!
```

- Flow chart:

```mermaid
flowchart LR
    markdown["`This ** is ** _Markdown_`"]
    newLines["`Line1
    Line 2
    Line 3`"]
    markdown --> newLines
```

or

```mermaid
flowchart LR
    Logger["LogManager"] --> TaskA["logger.get_logger('data_preprocessing')"]
    Logger --> TaskB["logger.get_logger('model_training')"]
    TaskA -->|writes| FileA["preprocess.log"]
    TaskB -->|writes| FileB["training.log"]
```

Possible FlowChart orientations are:
TB: Top to bottom
TD: Top-down/ same as top to bottom
BT: Bottom to top
RL: Right to left
LR: Left to right

- Class diagram:

```mermaid
classDiagram
    note "From Duck till Zebra"
    Animal <|-- Duck
    note for Duck "can fly\\ncan swim\\ncan dive\\ncan help in debugging"
    Animal <|-- Fish
    Animal <|-- Zebra
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()
    Animal: +mate()
    class Duck{
        +String beakColor
        +swim()
        +quack()
    }
    class Fish{
        -int sizeInFeet
        -canEat()
    }
    class Zebra{
        +bool is_wild
        +run()
    }
```

- Pie chart:

```mermaid
pie showData
    title Key elements in Product X
    "Calcium" : 42.96
    "Potassium" : 50.05
    "Magnesium" : 10.01
    "Iron" : 5
```

- Quadrant chart:

```mermaid
quadrantChart
    title Reach and engagement of campaigns
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    Campaign A: [0.3, 0.6]
    Campaign B: [0.45, 0.23]
    Campaign C: [0.57, 0.69]
    Campaign D: [0.78, 0.34]
    Campaign E: [0.40, 0.34]
    Campaign F: [0.35, 0.78]
```

- Timeline:

```mermaid
timeline
    title History of Social Media Platform
    2002 : LinkedIn
    2004 : Facebook
        : Google
    2005 : YouTube
    2006 : Twitter
```

- Radar chart:

```mermaid
radar-beta
    axis m["Math"], s["Science"], e["English"]
    axis h["History"], g["Geography"], a["Art"]
    curve a["Alice"]{85, 90, 80, 70, 75, 90}
    curve b["Bob"]{70, 75, 85, 80, 90, 85}
    max 100
    min 0
```
"""

    def _get_generation_system_prompt(self) -> str:
        """Get the system prompt for mermaid diagram generation."""
        return f"""
You are a specialized agent that enhances Markdown documents by inserting syntactically correct Mermaid diagrams.

**Core Responsibilities:**
- Insert Mermaid diagrams ONLY in appropriate locations within speaker notes sections
- Do NOT modify any existing Markdown content
- Ensure all Mermaid syntax is valid and renderable
- Limit to one diagram per slide unless explicitly needed

**Mermaid Code Block Rules:**
- Opening: ```mermaid (exactly three backticks + "mermaid")
- Closing: ``` (exactly three backticks only)
- NO nested or duplicate backticks within diagram content
- Newlines before and after the entire code block

**Syntax Requirements:**
- Use --> for arrows (NOT -- > or other variations)
- Node IDs: alphanumeric only, no spaces
- Labels: Use A["Label"] or A[Label] format consistently
- Quotes: Avoid double quotes in labels when possible
- Flowcharts: Must start with "flowchart" + orientation (LR, TD, etc.)
- Class diagrams: Use proper --> syntax for relationships

**Diagram Selection Guidelines:**
Choose appropriate diagram types based on content:
- Process flows → Flowchart
- System interactions → Sequence diagram
- Data structures → Class diagram
- Comparisons → Quadrant chart
- Timeline data → Timeline diagram
- Statistics → Pie chart

**Quality Standards:**
- All diagrams must be syntactically correct
- Nodes and relationships must be clearly defined
- Diagram type must match the content being illustrated
- Keep diagrams simple and focused

{self.few_shot_examples}
"""

    def _get_generation_user_prompt(self, slide_content: str) -> str:
        """
        Generate user prompt for mermaid diagram generation.

        Args:
            slide_content: Markdown content to enhance with diagrams

        Returns:
            Formatted user prompt string
        """
        return f"""
Enhance this Markdown document by inserting relevant Mermaid diagrams where they add value.

Rules:
- Insert diagrams within speaker notes sections only
- One diagram per slide maximum, unless multiple are clearly needed
- Ensure syntactically correct Mermaid code
- Do not modify existing content

Markdown content:
{slide_content}
"""

    def _get_validation_system_prompt(self) -> str:
        """Get the system prompt for mermaid diagram validation."""
        return """
You are a specialized agent responsible for validating and correcting Mermaid diagrams embedded in Markdown documents.
Your responsibilities are:

1. **Scope of Modification**
- Do **not** modify any non-Mermaid content in the Markdown.
- Only process Mermaid code blocks that contain syntax errors or invalid structures.
- Do **not** insert new diagrams, only fix existing ones.

2. **Code Block Structure Validation**
- Ensure each Mermaid diagram is properly enclosed: ```mermaid at start, ``` at end
- Verify there are no duplicate or nested backticks within the diagram content
- Ensure proper newlines before and after code blocks

3. **Syntax Validation & Common Fixes**
- Fix invalid Mermaid syntax according to official Mermaid documentation
- Replace invalid arrow syntax: Use --> instead of -- >
- Fix node labeling: Use proper syntax for labels (A["Label"] or A[Label])
- Correct relationship syntax in class diagrams: Use --> instead of -- >
- Fix flowchart syntax: Ensure proper node definitions and connections
- Validate diagram types and their specific syntax requirements

4. **Specific Error Patterns to Fix**
- Invalid arrows: `-- >` → `-->`
- Malformed node labels with quotes: Escape or remove problematic quotes
- Invalid class diagram relationships: Fix inheritance and association syntax
- Flowchart orientation errors: Ensure valid orientations (TB, TD, BT, RL, LR)
- Timeline syntax errors: Fix section and event formatting

5. **Validation Rules**
- Flowcharts must start with `flowchart` or `graph` followed by orientation
- Class diagrams must start with `classDiagram`
- Sequence diagrams must start with `sequenceDiagram`
- All node IDs must be valid (alphanumeric, no spaces)
- String literals should use consistent quoting (prefer no quotes when possible)
"""

    def _get_validation_user_prompt(self, content: str) -> str:
        """
        Generate user prompt for mermaid diagram validation.

        Args:
            content: Content with mermaid diagrams to validate

        Returns:
            Formatted user prompt string
        """
        return f"""
Please validate and fix the Mermaid diagrams in the following Markdown document.

Focus on these common issues:
1. Duplicate or malformed ``` lines
2. Invalid arrow syntax (-- > should be -->)
3. Incorrect node labeling or relationships
4. Invalid diagram type declarations
5. Syntax errors that prevent rendering

Apply fixes only where necessary to ensure diagrams are syntactically correct and renderable.
Do not modify any non-Mermaid content.

Markdown document to validate:
{content}
"""

    def _get_response(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 10000, model: str = "gpt-oss-120b"
    ) -> Tuple[str, Any]:
        """
        Get LLM response for mermaid processing.

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

        print(f"Mermaid processing response:\n{llm_response}")
        print(f"Prompt tokens used: {llm_usage.prompt_tokens}")
        print(f"Completion tokens used: {llm_usage.completion_tokens}")
        print(f"Total tokens used: {llm_usage.total_tokens}")

        return llm_response, llm_usage

    def clean_mermaid_blocks(self, content: str) -> str:
        """
        Clean up malformed mermaid code blocks to prevent duplicate ``` lines
        and ensure proper formatting.

        Args:
            content: Content with potentially malformed mermaid blocks

        Returns:
            Cleaned content with properly formatted mermaid blocks
        """
        # Pattern to find mermaid code blocks (including malformed ones)
        # This handles cases where there might be extra ``` lines
        pattern = r"```mermaid\n(.*?)\n```(?:\n```)*"

        def fix_mermaid_block(match):
            mermaid_content = match.group(1).strip()

            # Remove any stray ``` lines within the content
            lines = mermaid_content.split("\n")
            cleaned_lines = []

            for line in lines:
                stripped_line = line.strip()
                # Skip lines that are just backticks
                if stripped_line == "```" or stripped_line == "``````" or stripped_line.startswith("```"):
                    continue
                cleaned_lines.append(line)

            # Rejoin the cleaned content
            cleaned_content = "\n".join(cleaned_lines)

            # Return properly formatted mermaid block
            return f"```mermaid\n{cleaned_content}\n```"

        # Apply the fix to all mermaid blocks
        cleaned_content = re.sub(pattern, fix_mermaid_block, content, flags=re.DOTALL)

        # Additional cleanup: remove any standalone ``` lines that might be left
        lines = cleaned_content.split("\n")
        final_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # If we find a standalone ``` line, check if it's not part of a proper code block
            if line.strip() == "```":
                # Look back to see if this might be closing a code block
                prev_code_block = False
                for j in range(i - 1, max(-1, i - 10), -1):
                    if j >= 0 and lines[j].strip().startswith("```"):
                        prev_code_block = True
                        break

                # If it's not properly closing a code block, skip it
                if not prev_code_block:
                    i += 1
                    continue

            final_lines.append(line)
            i += 1

        return "\n".join(final_lines)

    def generate_mermaid_diagrams(self, slide_content: str) -> Tuple[str, Any]:
        """
        Generate mermaid diagrams for slide content.

        Args:
            slide_content: Markdown slide content to enhance

        Returns:
            Tuple of (enhanced_content, usage_info)
        """
        system_prompt = self._get_generation_system_prompt()
        user_prompt = self._get_generation_user_prompt(slide_content)

        enhanced_content, usage = self._get_response(system_prompt, user_prompt)
        return enhanced_content, usage

    def validate_and_fix_diagrams(self, content: str) -> Tuple[str, Any]:
        """
        Validate and fix mermaid diagrams in content.

        Args:
            content: Content with mermaid diagrams to validate

        Returns:
            Tuple of (validated_content, usage_info)
        """
        # First clean up malformed blocks
        cleaned_content = self.clean_mermaid_blocks(content)

        # Then validate and fix syntax
        system_prompt = self._get_validation_system_prompt()
        user_prompt = self._get_validation_user_prompt(cleaned_content)

        validated_content, usage = self._get_response(system_prompt, user_prompt)
        return validated_content, usage

    def process_mermaid_diagrams(self, slide_content: str) -> Tuple[str, dict]:
        """
        Complete mermaid processing pipeline: generation + cleanup + validation.

        Args:
            slide_content: Original slide content

        Returns:
            Tuple of (final_content, usage_stats)
        """
        # Step 1: Generate mermaid diagrams
        enhanced_content, generation_usage = self.generate_mermaid_diagrams(slide_content)

        # Step 2: Validate and fix diagrams
        final_content, validation_usage = self.validate_and_fix_diagrams(enhanced_content)

        # Combine usage statistics
        total_usage = {
            "generation": generation_usage,
            "validation": validation_usage,
            "total_tokens": generation_usage.total_tokens + validation_usage.total_tokens,
        }

        return final_content, total_usage
