# %%
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from openai import OpenAI
from utilities import FileIO

from content import SlideContentGenerator
from mermaid import MermaidProcessor

# Import modular components
from structure import SlideStructureGenerator


# %% Configuration
class PresentationConfig:
    """Configuration class for presentation generation with flexible user inputs."""

    def __init__(
        self,
        output_filename: str,
        user_prompt: Optional[str] = None,
        input_file: Optional[str] = None,
        num_slides: int = 20,
        enable_mermaid: bool = True,
        output_dir: str = "./outputs",
    ):
        """
        Initialize presentation configuration.

        Args:
            output_filename: Name for the final PowerPoint file (without extension)
            user_prompt: User's presentation request (optional if input_filename provided)
            input_file: Path to reference markdown file (optional)
            num_slides: Number of slides to generate. Default is 20.
            enable_mermaid: Whether to include mermaid diagrams. Default is True.
            output_dir: Directory to save all outputs. Default is "./outputs"

        Raises:
            ValueError: If both input_filename and user_prompt are not provided.
            ValueError: If user_prompt is not provided when input_filename is None.
        """
        # Validation logic
        if not input_file and not user_prompt:
            raise ValueError("Either input_filename or user_prompt must be provided")

        if not input_file and not user_prompt:
            raise ValueError("user_prompt is required when no input_filename is provided")

        # Set core parameters
        self.input_file = input_file
        self.user_prompt = user_prompt or "Create a presentation to summarize the document."
        self.num_slides = num_slides
        self.enable_mermaid = enable_mermaid

        # Generate automatic file paths with intuitive naming
        self._setup_output_paths(output_filename, output_dir)

    def _setup_output_paths(self, output_filename: str, output_dir: str):
        """Setup all output file paths with automatic naming convention."""
        # Create timestamp for unique file identification
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean output filename (remove extension if provided)
        clean_name = Path(output_filename).stem

        # Create output directory structure
        self.output_dir = Path(output_dir)
        self.session_dir = self.output_dir / f"{clean_name}_{timestamp}"

        # Create directories if they don't exist
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Define all output file paths
        self.slide_content_filename = str(self.session_dir / f"{clean_name}_content.md")
        self.final_content_filename = str(self.session_dir / f"{clean_name}_final.md")
        self.output_pptx = str(self.session_dir / f"{clean_name}_basic.pptx")
        self.final_output_pptx = str(self.session_dir / f"{clean_name}.pptx")

        # Store the clean name for reference
        self.presentation_name = clean_name

    def get_summary(self) -> str:
        """Get a summary of the configuration."""
        summary = f"""
=== Presentation Configuration ===
Presentation Name: {self.presentation_name}
Input File: {self.input_filename or 'None (prompt-only generation)'}
User Prompt: {self.user_prompt}
Number of Slides: {self.num_slides}
Mermaid Diagrams: {'Enabled' if self.enable_mermaid else 'Disabled'}
Output Directory: {self.session_dir}
Final Output: {self.final_output_pptx}
==================================
"""
        return summary


# %% Utility Functions
def convert_to_ppt(input_filename, output_filename):
    """Convert markdown to ppt using pandoc"""
    try:
        subprocess.run(["pandoc", "-o", output_filename, input_filename], check=True)
        print(f"Successfully converted '{input_filename}' to '{output_filename}'.")
    except FileNotFoundError:
        print("Error: Pandoc is not installed or not found in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Pandoc failed with error: {e}")


def setup_openai_client():
    """Setup and return OpenAI client."""
    httpx_client = httpx.Client(verify=False)
    openai_api_key = os.getenv("API_KEY")
    open_api_url = "https://api.openai.com/v1"

    return OpenAI(api_key=openai_api_key, base_url=open_api_url, http_client=httpx_client)


# %% Main Presentation Generation Pipeline
def generate_presentation(config: PresentationConfig):
    """
    Main pipeline for generating PowerPoint presentations from user prompts and markdown.

    Args:
        config: Configuration object with all necessary parameters
    """
    print(config.get_summary())
    print("=== Starting Presentation Generation Pipeline ===")

    # Initialize OpenAI client
    client = setup_openai_client()

    # Initialize generators
    structure_gen = SlideStructureGenerator(client)
    content_gen = SlideContentGenerator(client)
    mermaid_proc = MermaidProcessor(client)

    # Step 1: Generate slide structure
    print("\n1. Generating slide structure...")
    slide_structure, structure_usage = structure_gen.generate_structure(
        user_prompt=config.user_prompt, markdown_path=config.input_filename, num_slides=config.num_slides
    )

    # Step 2: Generate slide content
    print("\n2. Generating slide content...")
    slide_content, content_usage = content_gen.generate_content(
        slide_structure=slide_structure, markdown_path=config.input_filename
    )

    # Save initial content and create basic PowerPoint
    FileIO.fwrite(config.slide_content_filename, slide_content)
    convert_to_ppt(config.slide_content_filename, config.output_pptx)
    print(f"Basic presentation saved: {config.output_pptx}")

    # Step 3: Process mermaid diagrams (if enabled)
    if not config.enable_mermaid:
        # Print usage statistics
        print("\n=== Usage Statistics ===")
        print(f"Structure generation tokens: {structure_usage.total_tokens}")
        print(f"Content generation tokens: {content_usage.total_tokens}")
        print(f"Total tokens used: {structure_usage.total_tokens + content_usage.total_tokens}")

    else:
        print("\n3. Processing mermaid diagrams...")
        final_content, mermaid_usage = mermaid_proc.process_mermaid_diagrams(slide_content)

        # Save final content with mermaid diagrams
        FileIO.fwrite(config.final_content_filename, final_content)
        convert_to_ppt(config.final_content_filename, config.final_output_pptx)

        print("\n=== Generation Complete ===")
        print(f"Enhanced presentation saved: {config.final_output_pptx}")

        # Print usage statistics
        print("\n=== Usage Statistics ===")
        print(f"Structure generation tokens: {structure_usage.total_tokens}")
        print(f"Content generation tokens: {content_usage.total_tokens}")
        print(f"Mermaid processing tokens: {mermaid_usage['total_tokens']}")
        print(f"Total tokens used: {structure_usage.total_tokens + content_usage.total_tokens + mermaid_usage['total_tokens']}")


# # %% Execution Examples
# def example_usage():
#     """Demonstrate different ways to use the presentation generator."""

#     # Example 1: With reference document and custom prompt
#     print("=== Example 1: Reference document + custom prompt ===")
#     config1 = PresentationConfig(
#         output_filename="utilities_summary",
#         input_filename="./test_files/sample_reference_02.md",
#         user_prompt="Create a presentation to summarize the key utilities described.",
#         num_slides=15
#     )
#     generate_presentation(config1)

#     # Example 2: Reference document only (uses default prompt)
#     print("\n=== Example 2: Reference document only ===")
#     config2 = PresentationConfig(
#         output_filename="document_summary",
#         input_filename="./test_files/sample_reference_02.md"
#     )
#     generate_presentation(config2)

#     # Example 3: Prompt only (no reference document)
#     print("\n=== Example 3: Prompt only ===")
#     config3 = PresentationConfig(
#         output_filename="ai_trends_2024",
#         user_prompt="Create a presentation about the latest trends in artificial intelligence for 2024, covering machine learning, deep learning, and practical applications.",
#         enable_mermaid=False  # Disable mermaid for prompt-only generation
#     )
#     generate_presentation(config3)

if __name__ == "__main__":
    config = PresentationConfig(
        output_filename="test_presentation",
        input_filename="./test_files/sample_reference_01.md",
        user_prompt="Create a presentation to summarize the key utilities described.",
        num_slides=10,
        output_dir="./test_files/outputs",
    )
    generate_presentation(config)
