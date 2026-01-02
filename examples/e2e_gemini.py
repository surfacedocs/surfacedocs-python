#!/usr/bin/env python3
"""
End-to-end test: Generate a document with Gemini and save to SurfaceDocs.

Usage:
    export GEMINI_API_KEY=your_key
    python examples/e2e_gemini.py
"""

import os
from google import genai
from google.genai import types

from surfacedocs import SurfaceDocs, GEMINI_DOCUMENT_SCHEMA, SYSTEM_PROMPT

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

    # Prompt for document generation
    prompt = """
Create a document about "Python Best Practices for API Development".
Include:
- A heading
- 2-3 paragraphs of content
- A code example
- A bullet list of key takeaways
"""

    print("Generating document with Gemini (using structured output)...")

    # Use native JSON schema - guarantees valid JSON output
    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=GEMINI_DOCUMENT_SCHEMA,
        ),
    )

    # No JSON parsing needed - response.text is guaranteed valid JSON
    document = response.parsed  # or json.loads(response.text)

    print(f"\nDocument title: {document.get('title')}")
    print(f"Block count: {len(document.get('blocks', []))}")
    for i, block in enumerate(document.get('blocks', [])):
        print(f"  Block {i+1}: {block.get('type')}")

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
