#!/usr/bin/env python3
"""Quick start: Anthropic → SurfaceDocs using tool use."""
import os
import anthropic
from surfacedocs import SurfaceDocs, DOCUMENT_SCHEMA, SYSTEM_PROMPT

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=SYSTEM_PROMPT,
    messages=[
        {"role": "user", "content": "Write a quick guide on Python virtual environments."},
    ],
    tools=[
        {
            "name": "create_document",
            "description": "Create a structured document for SurfaceDocs",
            "input_schema": DOCUMENT_SCHEMA,
        }
    ],
    tool_choice={"type": "tool", "name": "create_document"},
)

# Extract tool use result
tool_use = next(block for block in response.content if block.type == "tool_use")

docs = SurfaceDocs(
    api_key="sd_live_JBycgl5WHhtzVyeB9jQf7172dKvq06FX",
    base_url="https://ingress.dev.surfacedocs.dev",
)
result = docs.save(tool_use.input, folder_id="VZW8T4l44jOuVEZ4952w")
print(result.url)
