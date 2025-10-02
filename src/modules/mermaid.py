"""
Mermaid Diagram Generation and Validation Module

This module handles the generation, cleanup, and validation of mermaid diagrams
for PowerPoint presentations.
"""

import re
from typing import Any, Tuple

from .llm_utils import LLMUtils


class MermaidProcessor:
    """Handles mermaid diagram generation, cleanup, and validation."""

    def __init__(self, client):
        """
        Initialize the mermaid processor.

        Args:
            client: OpenAI client instance for API calls
        """
        self.client = client

    @property
    def few_shot_examples(self) -> str:
        """
        Get the few-shot examples for mermaid diagram generation.

        Returns:
            Formatted examples string
        """
        return """
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

- Gantt chart:

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title       Adding GANTT diagram functionality to mermaid
    excludes    weekends
    %% (`excludes` accepts specific dates in YYYY-MM-DD format, days of the week ("sunday") or "weekends", but not the word "weekdays".)

    section A section
    Completed task            :done,    des1, 2014-01-06,2014-01-08
    Active task               :active,  des2, 2014-01-09, 3d
    Future task               :         des3, after des2, 5d
    Future task2              :         des4, after des3, 5d

    section Critical tasks
    Completed task in the critical line :crit, done, 2014-01-06,24h
    Implement parser and jison          :crit, done, after des1, 2d
    Create tests for parser             :crit, active, 3d
    Future task in critical line        :crit, 5d
    Create tests for renderer           :2d
    Add to mermaid                      :until isadded
    Functionality added                 :milestone, isadded, 2014-01-25, 0d
```

"""

    @property
    def generation_system_prompt(self) -> str:
        """Get the system prompt for mermaid diagram generation."""
        return f"""
You are a specialized agent that enhances Markdown documents by inserting syntactically correct Mermaid diagrams.

**Core Responsibilities:**
- Insert Mermaid diagrams ONLY in appropriate locations within speaker notes sections
- Do NOT modify any existing Markdown content
- Ensure all Mermaid syntax is valid and renderable
- Limit to one diagram per slide unless explicitly needed
- Skip diagram insertion if content is already clear without visual aid
- Convert any timeline or gantt chart table into proper Mermaid Gantt Chart syntax

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
- Process flows: Flowchart
- System interactions: Sequence diagram
- Data structures: Class diagram
- Comparisons: Quadrant chart
- Timeline data: Timeline diagram
- Project schedules: Gantt chart
- Statistics: Pie chart

**Quality Standards:**
- All diagrams must be syntactically correct
- Nodes and relationships must be clearly defined
- Diagram type must match the content being illustrated
- Keep diagrams simple and focused

**Few-shot examples:**
{self.few_shot_examples}
"""

    @staticmethod
    def _get_generation_user_prompt(slide_content: str) -> str:
        """
        Generate user prompt for mermaid diagram generation.

        Args:
            slide_content: Markdown content to enhance with diagrams

        Returns:
            Formatted user prompt string
        """
        return f"""
Analyze this Markdown document and insert Mermaid diagrams ONLY where they provide significant visual value.

Critical Rules:
- Only add diagrams if they enhance understanding beyond the text, or would benefit from a visual aid
e.g., visualizing a process, structure, timeline, comparison, statistics, summary, etc.
- Skip if content is already clear and well-structured
- Insert diagrams within speaker notes sections only
- One diagram per slide maximum, unless multiple are clearly needed
- Ensure syntactically correct Mermaid code
- Do not modify existing content

Markdown content:
{slide_content}
"""

    @property
    def validation_system_prompt(self) -> str:
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

3. **Node Labeling Syntax (CRITICAL)**
- Node labels with special characters, spaces, parentheses, or HTML tags MUST be quoted
- Use double quotes for labels: NodeID["Label with spaces/special chars"]
- Examples of REQUIRED quoting:
  * Start["signal received<br/>(sigint / sigterm)"] ✓
  * Start[signal received<br/>(sigint / sigterm)] ✗ (INVALID)
  * Cleanup["_cleanup()"] ✓
  * Cleanup[_cleanup()] ✗ (INVALID if contains special chars)
- Simple alphanumeric labels can be unquoted: NodeID[SimpleLabel] or NodeID["SimpleLabel"]

4. **Syntax Validation & Common Fixes**
- Fix invalid Mermaid syntax according to official Mermaid documentation
- Replace invalid arrow syntax: Use --> instead of -- >
- Fix node labeling: Ensure all labels with special characters are properly quoted
- Correct relationship syntax in class diagrams: Use --> instead of -- >
- Fix flowchart syntax: Ensure proper node definitions and connections
- Validate diagram types and their specific syntax requirements

5. **Specific Error Patterns to Fix**
- Invalid arrows: `-- >` → `-->`
- Unquoted labels with special characters: `Node[label(with)special]` → `Node["label(with)special"]`
- Unquoted labels with spaces: `Node[my label]` → `Node["my label"]`
- Unquoted labels with HTML: `Node[text<br/>more]` → `Node["text<br/>more"]`
- Invalid class diagram relationships: Fix inheritance and association syntax
- Flowchart orientation errors: Ensure valid orientations (TB, TD, BT, RL, LR)
- Timeline syntax errors: Fix section and event formatting

6. **Validation Rules**
- Flowcharts must start with `flowchart` or `graph` followed by orientation
- Class diagrams must start with `classDiagram`
- Sequence diagrams must start with `sequenceDiagram`
- All node IDs must be valid (alphanumeric, no spaces)
- Any label containing spaces, parentheses, brackets, HTML tags, or special characters MUST be quoted

7. **Output Requirement**
- You must always return the entire markdown document, including both modified and unmodified content, even if no changes are made.
- Never summarize, omit, or skip any sections. Do not reply with explanations or comments—only output the full markdown document.
"""

    @staticmethod
    def _get_validation_user_prompt(content: str) -> str:
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
3. **CRITICAL: Unquoted node labels with special characters**
   - Labels with spaces, parentheses, HTML tags, or special chars MUST be quoted
   - Fix: Start[signal received<br/>(sigint)] → Start["signal received<br/>(sigint)"]
   - Fix: Cleanup[_cleanup()] → Cleanup["_cleanup()"]
4. Incorrect node labeling or relationships
5. Invalid diagram type declarations
6. Syntax errors that prevent rendering

- Only fix Mermaid code blocks with errors.
- Do not modify any non-Mermaid content.
- Return the entire markdown document, even if no changes are needed.

Markdown document to validate:
{content}
"""

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
        pattern = r"```mermaid\n(.*?)\n```(?:\n*```)*"

        def fix_mermaid_block(match):
            """
            Clean and reformat a matched Mermaid code block.

            Args:
                match: A regex match object for a Mermaid code block.

            Returns:
                A string with the cleaned and properly formatted Mermaid code block.
            """
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

        # Replace every match of pattern with the result of fix_mermaid_block
        # Apply the fix to all mermaid blocks
        return re.sub(pattern, fix_mermaid_block, content, flags=re.DOTALL)

    @staticmethod
    def validate_notes_closure(content: str) -> Tuple[bool, list]:
        """
        Validate that all ::: notes sections are properly closed before the next slide.

        Args:
            content: Markdown content to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        lines = content.split("\n")
        errors = []
        notes_open = False
        slide_number = 1

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for slide separator
            if stripped == "---":
                if notes_open:
                    errors.append(f"Slide {slide_number}: Notes section not closed before slide separator at line {i}")
                    notes_open = False
                slide_number += 1

            # Check for notes opening
            elif stripped.startswith("::: notes"):
                if notes_open:
                    errors.append(f"Slide {slide_number}: Notes section already open at line {i}")
                notes_open = True

            # Check for notes closing
            elif stripped == ":::":
                if not notes_open:
                    errors.append(f"Slide {slide_number}: Closing ::: without opening notes section at line {i}")
                else:
                    notes_open = False

        # Check if notes are still open at end of content
        if notes_open:
            errors.append(f"Slide {slide_number}: Notes section not closed at end of document")

        return len(errors) == 0, errors

    def generate_mermaid_diagrams(self, slide_content: str) -> Tuple[str, Any]:
        """
        Generate mermaid diagrams for slide content.

        Args:
            slide_content: Markdown slide content to enhance

        Returns:
            Tuple of (enhanced_content, usage_info)
        """
        system_prompt = self.generation_system_prompt
        user_prompt = self._get_generation_user_prompt(slide_content)

        enhanced_content, usage = LLMUtils.get_response(self.client, system_prompt, user_prompt, context="Mermaid generation")
        return enhanced_content, usage

    def validate_and_fix_diagrams(self, content: str) -> Tuple[str, Any]:
        """
        Validate and fix mermaid diagrams in content.

        Args:
            content: Content with mermaid diagrams to validate

        Returns:
            Tuple of (validated_content, usage_info)
        """
        # First validate and fix syntax
        system_prompt = self.validation_system_prompt
        user_prompt = self._get_validation_user_prompt(content)

        validated_content, usage = LLMUtils.get_response(self.client, system_prompt, user_prompt, context="Mermaid validation")

        # Then clean up malformed blocks
        cleaned_content = self.clean_mermaid_blocks(validated_content)
        cleaned_content = self.validate_notes_closure(cleaned_content)

        return cleaned_content, usage

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

        return enhanced_content, final_content, total_usage
