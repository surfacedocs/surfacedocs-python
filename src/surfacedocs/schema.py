"""JSON schema for LLM structured output.

This schema is designed to work with:
- OpenAI's response_format (json_schema)
- Anthropic's tools (input_schema)
- Google Gemini's response_schema

Block Type Metadata:
    heading     - level: int (1-6)
    paragraph   - (none)
    code        - language: str (optional, e.g., "python", "javascript")
    list        - listType: str ("bullet" or "ordered")
    quote       - (none)
    table       - (none - content is markdown table format)
    image       - url: str (required), alt: str (optional)
    divider     - (none)
"""

DOCUMENT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Document title",
            "maxLength": 500,
        },
        "metadata": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Identifier for the agent/system that created this document",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for categorization",
                },
            },
            "additionalProperties": True,
        },
        "blocks": {
            "type": "array",
            "description": "Content blocks that make up the document",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "heading",
                            "paragraph",
                            "code",
                            "list",
                            "quote",
                            "table",
                            "image",
                            "divider",
                        ],
                        "description": "Block type",
                    },
                    "content": {
                        "type": "string",
                        "description": "Block content (markdown for text, code for code blocks, etc.)",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Block-specific metadata (level for headings, language for code, etc.)",
                    },
                },
                "required": ["type", "content"],
            },
        },
    },
    "required": ["title", "blocks"],
}

# OpenAI-compatible schema (strict mode requires additionalProperties: false and all properties required)
OPENAI_DOCUMENT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Document title",
        },
        "metadata": {
            "type": "object",
            "properties": {
                "source": {
                    "type": ["string", "null"],
                    "description": "Identifier for the agent/system that created this document",
                },
                "tags": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "Optional tags for categorization",
                },
            },
            "required": ["source", "tags"],
            "additionalProperties": False,
        },
        "blocks": {
            "type": "array",
            "description": "Content blocks that make up the document",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "heading",
                            "paragraph",
                            "code",
                            "list",
                            "quote",
                            "table",
                            "image",
                            "divider",
                        ],
                        "description": "Block type",
                    },
                    "content": {
                        "type": "string",
                        "description": "Block content (markdown for text, code for code blocks, etc.)",
                    },
                    "metadata": {
                        "type": ["object", "null"],
                        "description": "Block-specific metadata (level for headings, language for code, etc.)",
                        "properties": {
                            "level": {
                                "type": ["integer", "null"],
                                "description": "Heading level (1-6), only for heading blocks",
                            },
                            "language": {
                                "type": ["string", "null"],
                                "description": "Programming language, only for code blocks",
                            },
                            "listType": {
                                "type": ["string", "null"],
                                "enum": ["bullet", "ordered", None],
                                "description": "List type, only for list blocks",
                            },
                            "url": {
                                "type": ["string", "null"],
                                "description": "Image URL, only for image blocks",
                            },
                            "alt": {
                                "type": ["string", "null"],
                                "description": "Image alt text, only for image blocks",
                            },
                        },
                        "required": ["level", "language", "listType", "url", "alt"],
                        "additionalProperties": False,
                    },
                },
                "required": ["type", "content", "metadata"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "metadata", "blocks"],
    "additionalProperties": False,
}

# Gemini-compatible schema (no additionalProperties, explicit metadata fields)
GEMINI_DOCUMENT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Document title",
        },
        "blocks": {
            "type": "array",
            "description": "Content blocks that make up the document",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "heading",
                            "paragraph",
                            "code",
                            "list",
                            "quote",
                            "table",
                            "image",
                            "divider",
                        ],
                        "description": "Block type",
                    },
                    "content": {
                        "type": "string",
                        "description": "Block content (markdown for text, code for code blocks, etc.)",
                    },
                    "level": {
                        "type": "integer",
                        "description": "Heading level (1-6), only for heading blocks",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language, only for code blocks",
                    },
                    "listType": {
                        "type": "string",
                        "enum": ["bullet", "ordered"],
                        "description": "List type, only for list blocks",
                    },
                },
                "required": ["type", "content"],
            },
        },
    },
    "required": ["title", "blocks"],
}
