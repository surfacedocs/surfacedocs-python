"""System prompt for LLM document generation.

This prompt instructs LLMs to output JSON documents matching DOCUMENT_SCHEMA.

Usage with OpenAI:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Document the authentication flow"},
    ]

Usage with Anthropic:
    response = client.messages.create(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Document the authentication flow"}],
        ...
    )
"""

SYSTEM_PROMPT: str = """When asked to create documentation, respond with a JSON document using this structure:

{
  "title": "Document title",
  "metadata": {
    "source": "agent-name",
    "tags": ["optional", "tags"]
  },
  "blocks": [
    {"type": "heading", "content": "Section Header", "metadata": {"level": 1}},
    {"type": "paragraph", "content": "Body text with **bold** and *italic*."},
    {"type": "code", "content": "print('hello')", "metadata": {"language": "python"}},
    {"type": "list", "content": "- Item 1\\n- Item 2", "metadata": {"listType": "bullet"}},
    {"type": "quote", "content": "A notable quote."},
    {"type": "table", "content": "| Col1 | Col2 |\\n|------|------|\\n| a | b |"},
    {"type": "divider", "content": ""}
  ]
}

Block types:
- heading: Section header (metadata.level: 1-6)
- paragraph: Body text with inline markdown
- code: Code block (metadata.language optional)
- list: Markdown list (metadata.listType: "bullet" or "ordered")
- quote: Block quote
- table: Markdown table format
- image: Image (metadata.url required, metadata.alt optional)
- divider: Horizontal rule

Text fields support inline markdown: **bold**, *italic*, `code`, [link](url)"""
