#!/usr/bin/env python3
"""Quick start: OpenAI → SurfaceDocs using structured output."""
from openai import OpenAI
from surfacedocs import SurfaceDocs, OPENAI_DOCUMENT_SCHEMA, SYSTEM_PROMPT

client = OpenAI()  # Uses OPENAI_API_KEY env var

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Write a quick guide on Python virtual environments."},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "surfacedocs_document",
            "strict": True,
            "schema": OPENAI_DOCUMENT_SCHEMA,
        },
    },
)

docs = SurfaceDocs(
    api_key="sd_live_JBycgl5WHhtzVyeB9jQf7172dKvq06FX",
    base_url="https://ingress.dev.surfacedocs.dev",
)
result = docs.save(response.choices[0].message.content, folder_id="VZW8T4l44jOuVEZ4952w")
print(result.url)
