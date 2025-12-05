import base64
import hashlib
import os
import re
from typing import Optional

import httpx


class MermaidRenderer:
    """
    Handles rendering of Mermaid diagrams to images and injecting them into Markdown slides.
    Uses mermaid.ink service for conversion to keep dependencies minimal.
    """

    def __init__(self, images_dir: str = "images"):
        """
        Initialize the renderer.

        Args:
            images_dir: Directory to store generated images
        """
        self.images_dir = images_dir
        os.makedirs(self.images_dir, exist_ok=True)

    def _render_to_file(self, mermaid_code: str) -> Optional[str]:
        """
        Renders mermaid code to PNG and returns the file path.

        Args:
            mermaid_code: The mermaid diagram syntax

        Returns:
            Path to the generated image file, or None if failed
        """
        # Generate hash for filename to avoid duplicates/re-rendering
        code_hash = hashlib.md5(mermaid_code.strip().encode("utf-8")).hexdigest()
        filename = f"mermaid_{code_hash}.png"
        filepath = os.path.join(self.images_dir, filename)

        # Return existing if already generated
        if os.path.exists(filepath):
            return filepath.replace("\\", "/")

        # Encode for mermaid.ink
        # mermaid.ink expects base64 encoding of the diagram code
        # We use urlsafe_b64encode to ensure the string is URL-safe
        graphbytes = mermaid_code.strip().encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")

        url = f"https://mermaid.ink/img/{base64_string}"

        try:
            # Use httpx as it's already in requirements
            response = httpx.get(url, timeout=10.0)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath.replace("\\", "/")
            else:
                print(f"Mermaid.ink returned status {response.status_code}")
        except Exception as e:
            print(f"Failed to render mermaid diagram: {e}")

        return None

    def process_slides(self, content: str) -> str:
        """
        Scans markdown content for mermaid blocks in notes,
        renders them, and inserts image links into the slide body.

        Args:
            content: The full markdown content

        Returns:
            Markdown content with inserted image links
        """
        # Split by slides to handle context correctly
        # We use capturing group to keep the separators
        slides = re.split(r"(^---$)", content, flags=re.MULTILINE)
        processed_slides = []

        for slide in slides:
            if slide.strip() == "---":
                processed_slides.append(slide)
                continue

            # Find mermaid block in notes
            # Look for ::: notes ... ```mermaid ... ``` ... :::
            notes_match = re.search(r"(::: notes[\s\S]*?:::)", slide)

            if notes_match:
                notes_content = notes_match.group(1)
                # Find mermaid code inside notes
                mermaid_match = re.search(r"```mermaid\n([\s\S]*?)\n```", notes_content)

                if mermaid_match:
                    mermaid_code = mermaid_match.group(1)
                    image_path = self._render_to_file(mermaid_code)

                    if image_path:
                        # Insert image before the notes section
                        # We split the slide by the notes content to insert before it
                        parts = slide.split(notes_content)

                        # parts[0] is the slide body
                        # parts[1] is anything after notes (usually empty)

                        # Add image at the end of slide body
                        # We add newlines to ensure separation
                        new_slide_body = f"{parts[0].rstrip()}\n\n![]({image_path})\n\n"

                        # Reconstruct slide
                        slide = f"{new_slide_body}{notes_content}{parts[1] if len(parts) > 1 else ''}"

            processed_slides.append(slide)

        return "".join(processed_slides)
