#!/usr/bin/env python3
"""Minimal example: LLM output → SurfaceDocs in ~10 lines."""
import os
from google import genai
from google.genai import types
from surfacedocs import SurfaceDocs, GEMINI_DOCUMENT_SCHEMA, SYSTEM_PROMPT

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents="Write a quick guide on Python virtual environments.",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=GEMINI_DOCUMENT_SCHEMA,
    ),
)

docs = SurfaceDocs(api_key="sd_live_JBycgl5WHhtzVyeB9jQf7172dKvq06FX", base_url="https://ingress.dev.surfacedocs.dev")
result = docs.save(response.text, folder_id="VZW8T4l44jOuVEZ4952w")
print(result.url)
