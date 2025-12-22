# Manual Config Updates Required

Due to file editing issues, please manually update `config.py` with the following changes:

## Line 10: Change default provider
```python
# BEFORE:
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# AFTER:
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "asu_ai")
```

## Line 26: Enable ASU AI by default
```python
# BEFORE:
ASU_AI_ENABLED = os.getenv("ASU_AI_ENABLED", "false").lower() == "true"

# AFTER:
ASU_AI_ENABLED = os.getenv("ASU_AI_ENABLED", "true").lower() == "true"
```

## Line 29: Change default model to gpt-40
```python
# BEFORE:
ASU_AI_MODEL = os.getenv("ASU_AI_MODEL", "gpt-4o-mini")

# AFTER:
ASU_AI_MODEL = os.getenv("ASU_AI_MODEL", "gpt-4o")
```

## Line 30: Add embedding model (add new line)
```python
ASU_AI_EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embeddings
```

Save the file after making these 4 changes.
