# SurfaceDocs Python SDK

Python SDK for SurfaceDocs - Save LLM-generated documents.

## Installation

```bash
pip install surfacedocs
```

## Quick Start

```python
from surfacedocs import SurfaceDocs, DOCUMENT_SCHEMA, SYSTEM_PROMPT
from openai import OpenAI

# Initialize clients
openai = OpenAI()
docs = SurfaceDocs(api_key="sd_live_...")

# User handles their own LLM call
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Document our REST API authentication flow"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "surfacedocs_document",
            "schema": DOCUMENT_SCHEMA,
        },
    },
)

# Save to SurfaceDocs
result = docs.save(response.choices[0].message.content)
print(result.url)  # https://app.surfacedocs.dev/d/abc123
```

## Documentation

See the [full documentation](https://surfacedocs.dev/docs) for more details.

## License

MIT
