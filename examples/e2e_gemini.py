#!/usr/bin/env python3
"""
End-to-end test: Generate a document with Gemini and save to SurfaceDocs.

Usage:
    export GEMINI_API_KEY=your_key
    python examples/e2e_gemini.py
"""

import os
import json
from google import genai

from surfacedocs import SurfaceDocs, DOCUMENT_SCHEMA, SYSTEM_PROMPT

# Configuration
SURFACEDOCS_API_KEY = "sd_live_JBycgl5WHhtzVyeB9jQf7172dKvq06FX"
SURFACEDOCS_BASE_URL = "https://ingress.dev.surfacedocs.dev"
SURFACEDOCS_FOLDER_ID = "VZW8T4l44jOuVEZ4952w"


def main():
    # Initialize Gemini
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("Set GEMINI_API_KEY environment variable")

    client = genai.Client(api_key=gemini_api_key)

    # Build prompt for Gemini
    prompt = f"""
{SYSTEM_PROMPT}

Now, create a document about "Python Best Practices for API Development".
Include:
- A heading
- 2-3 paragraphs of content
- A code example
- A bullet list of key takeaways

Respond with ONLY the JSON document, no other text.
"""

    print("Generating document with Gemini...")
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
    )

    # Extract JSON from response
    response_text = response.text.strip()

    # Handle markdown code blocks if present
    if response_text.startswith("```"):
        # Remove ```json and ``` markers
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    print(f"Gemini response:\n{response_text[:500]}...")

    # Parse and validate
    try:
        document = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {response_text}")
        raise

    print(f"\nDocument title: {document.get('title')}")
    print(f"Block count: {len(document.get('blocks', []))}")

    # Save to SurfaceDocs
    print("\nSaving to SurfaceDocs...")
    docs = SurfaceDocs(api_key=SURFACEDOCS_API_KEY, base_url=SURFACEDOCS_BASE_URL)

    result = docs.save(
        content=document,
        folder_id=SURFACEDOCS_FOLDER_ID,
    )

    print(f"\n✓ Document saved successfully!")
    print(f"  ID: {result.id}")
    print(f"  URL: {result.url}")
    print(f"  Folder: {result.folder_id}")


if __name__ == "__main__":
    main()
