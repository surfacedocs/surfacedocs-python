# SurfaceDocs Python SDK

Save LLM-generated documents to [SurfaceDocs](https://surfacedocs.dev).

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

# Generate a document with your LLM
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

## What's Included

The SDK provides three exports:

| Export | Type | Purpose |
|--------|------|---------|
| `DOCUMENT_SCHEMA` | dict | JSON schema for LLM structured output |
| `SYSTEM_PROMPT` | str | Instructions for LLM to generate documents |
| `SurfaceDocs` | class | HTTP client to save documents |

## API Reference

### SurfaceDocs

```python
from surfacedocs import SurfaceDocs

# Initialize with API key
client = SurfaceDocs(api_key="sd_live_...")

# Or use environment variable
# export SURFACEDOCS_API_KEY=sd_live_...
client = SurfaceDocs()
```

#### save(content, folder_id=None)

Save a document from LLM output.

```python
# From JSON string
result = client.save(response.choices[0].message.content)

# From dict
result = client.save({
    "title": "My Document",
    "blocks": [{"type": "paragraph", "content": "Hello world"}]
})

# To specific folder
result = client.save(content, folder_id="folder_abc123")
```

#### save_raw(title, blocks, folder_id=None, metadata=None)

Save a document with explicit parameters.

```python
result = client.save_raw(
    title="API Documentation",
    blocks=[
        {"type": "heading", "content": "Authentication", "metadata": {"level": 1}},
        {"type": "paragraph", "content": "Use Bearer tokens for auth."},
        {"type": "code", "content": "curl -H 'Authorization: Bearer ...'", "metadata": {"language": "bash"}},
    ],
    metadata={"source": "doc-generator", "version": "1.0"},
)
```

#### get_document(document_id)

Retrieve a document by ID.

```python
doc = client.get_document("doc_abc123")
print(doc.title)                # "API Documentation"
print(doc.blocks[0].type)      # "heading"
print(doc.blocks[0].content)   # "Authentication"
```

#### delete_document(document_id)

Delete a document by ID.

```python
client.delete_document("doc_abc123")
```

#### create_folder(name, parent_id=None)

Create a new folder.

```python
folder = client.create_folder("API Docs")
print(folder.id)    # "fld_abc123"
print(folder.name)  # "API Docs"

# Create a subfolder
subfolder = client.create_folder("v2", parent_id=folder.id)
```

#### list_folders(parent_id=None)

List folders, optionally filtered by parent.

```python
# List all root folders
folders = client.list_folders()

# List subfolders of a specific folder
subfolders = client.list_folders(parent_id="fld_abc123")
```

#### SaveResult

Both `save()` and `save_raw()` return a `SaveResult`:

```python
result.id        # "doc_abc123"
result.url       # "https://app.surfacedocs.dev/d/doc_abc123"
result.folder_id # "folder_xyz"
```

#### Document

Returned by `get_document()`:

```python
doc.id            # "doc_abc123"
doc.url           # "https://app.surfacedocs.dev/d/doc_abc123"
doc.folder_id     # "folder_xyz"
doc.title         # "My Document"
doc.content_type  # "markdown"
doc.visibility    # "private"
doc.blocks        # list[Block]
doc.metadata      # dict or None
doc.created_at    # "2024-01-01T00:00:00Z"
doc.updated_at    # "2024-01-02T00:00:00Z"
```

#### Block

Each document contains a list of `Block` objects:

```python
block.id        # "blk_abc123"
block.order     # 0
block.type      # "heading", "paragraph", "code", etc.
block.content   # "Hello world"
block.metadata  # {"level": 1} or None
```

#### Folder

Returned by `create_folder()` and `list_folders()`:

```python
folder.id         # "fld_abc123"
folder.name       # "API Docs"
folder.parent_id  # "fld_parent" or None
folder.path       # "/API Docs"
folder.depth      # 0
folder.created_at # "2024-01-01T00:00:00Z"
```

### DOCUMENT_SCHEMA

JSON schema dict for LLM structured output. Pass directly to your LLM provider.

### SYSTEM_PROMPT

System prompt string to instruct LLMs on document format.

```python
from surfacedocs import SYSTEM_PROMPT

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Document the login flow"},
]
```

## Block Types

Documents are composed of blocks:

| Type | Description | Metadata |
|------|-------------|----------|
| `heading` | Section header | `level` (1-6) |
| `paragraph` | Body text | - |
| `code` | Code block | `language` (optional) |
| `list` | Bullet/numbered list | `listType` ("bullet" or "ordered") |
| `quote` | Block quote | - |
| `table` | Markdown table | - |
| `image` | Image | `url` (required), `alt` (optional) |
| `divider` | Horizontal rule | - |

Text content supports inline markdown: `**bold**`, `*italic*`, `` `code` ``, `[link](url)`

## Error Handling

```python
from surfacedocs import (
    SurfaceDocs,
    SurfaceDocsError,
    AuthenticationError,
    DocumentNotFoundError,
    FolderNotFoundError,
    ValidationError,
)

try:
    result = client.save(content)
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid document: {e}")
except SurfaceDocsError as e:
    print(f"API error: {e}")

try:
    doc = client.get_document("doc_abc123")
except DocumentNotFoundError:
    print("Document does not exist")

try:
    folder = client.create_folder("Docs", parent_id="fld_nonexistent")
except FolderNotFoundError:
    print("Parent folder does not exist")
```

## Environment Variables

```bash
# API key (alternative to passing in code)
export SURFACEDOCS_API_KEY=sd_live_...
```

## Examples

### OpenAI

```python
from surfacedocs import SurfaceDocs, DOCUMENT_SCHEMA, SYSTEM_PROMPT
from openai import OpenAI

openai = OpenAI()
docs = SurfaceDocs()

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Write documentation for user authentication"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "document", "schema": DOCUMENT_SCHEMA},
    },
)

result = docs.save(response.choices[0].message.content)
print(f"Saved: {result.url}")
```

### Anthropic

Using Claude's structured outputs with tool use:

```python
from surfacedocs import SurfaceDocs, DOCUMENT_SCHEMA, SYSTEM_PROMPT
import anthropic

client = anthropic.Anthropic()
docs = SurfaceDocs()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=SYSTEM_PROMPT,
    messages=[
        {"role": "user", "content": "Write documentation for user authentication"},
    ],
    tools=[{
        "name": "create_document",
        "description": "Create a structured document",
        "input_schema": DOCUMENT_SCHEMA,
    }],
    tool_choice={"type": "tool", "name": "create_document"},
)

tool_use = next(b for b in response.content if b.type == "tool_use")
result = docs.save(tool_use.input)
print(f"Saved: {result.url}")
```

### Google Gemini

Using Gemini's structured output with JSON schema:

```python
from surfacedocs import SurfaceDocs, DOCUMENT_SCHEMA, SYSTEM_PROMPT
import google.generativeai as genai

genai.configure(api_key="...")
docs = SurfaceDocs()

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=DOCUMENT_SCHEMA,
    ),
)

response = model.generate_content("Write documentation for user authentication")
result = docs.save(response.text)
print(f"Saved: {result.url}")
```

### Manual Document

```python
from surfacedocs import SurfaceDocs

docs = SurfaceDocs()

result = docs.save_raw(
    title="Meeting Notes",
    blocks=[
        {"type": "heading", "content": "Action Items", "metadata": {"level": 1}},
        {"type": "list", "content": "- Review PR #123\n- Update docs", "metadata": {"listType": "bullet"}},
        {"type": "divider", "content": ""},
        {"type": "paragraph", "content": "Next meeting: Monday 10am"},
    ],
    metadata={"source": "meeting-bot"},
)
```

### Managing Documents

```python
from surfacedocs import SurfaceDocs, DocumentNotFoundError

docs = SurfaceDocs()

# Save a document
result = docs.save_raw(
    title="API Guide",
    blocks=[{"type": "paragraph", "content": "Welcome to the API."}],
)

# Retrieve it
doc = docs.get_document(result.id)
print(doc.title)  # "API Guide"

# Delete it
docs.delete_document(result.id)
```

### Managing Folders

```python
from surfacedocs import SurfaceDocs

docs = SurfaceDocs()

# Create a folder hierarchy
parent = docs.create_folder("Engineering")
child = docs.create_folder("Backend", parent_id=parent.id)

# List root folders
for folder in docs.list_folders():
    print(folder.name)

# List subfolders
for folder in docs.list_folders(parent_id=parent.id):
    print(f"  {folder.name}")

# Save a document to a folder
result = docs.save_raw(
    title="Architecture Overview",
    blocks=[{"type": "paragraph", "content": "Our system uses..."}],
    folder_id=child.id,
)
```

## License

MIT
