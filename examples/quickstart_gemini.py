#!/usr/bin/env python3
"""Quick start: Gemini → SurfaceDocs using structured output."""
import os
from google import genai
from google.genai import types
from surfacedocs import SurfaceDocs, GEMINI_DOCUMENT_SCHEMA, SYSTEM_PROMPT

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Write a quick guide on Python virtual environments.",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=GEMINI_DOCUMENT_SCHEMA,
    ),
)

docs = SurfaceDocs(
    api_key="sd_live_RrJPC6LqO0CqSqnGeNnm93RHlXa8x6iS",
    base_url="https://ingress.surfacedocs.dev",
)
result = docs.save(response.text, folder_id="xEQ5xO0wt0g4Oj5cm07X")
print(result.url)
