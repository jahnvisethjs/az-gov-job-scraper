"""Keep the checked-in environment example aligned with runtime configuration."""

from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_env_example_contains_only_supported_settings():
    values = dotenv_values(PROJECT_ROOT / ".env.example")

    assert values == {
        "ASU_AI_ENABLED": "true",
        "ASU_AI_API_KEY": "",
        "ASU_AI_BASE_URL": "https://api-main.aiml.asu.edu",
        "ASU_AI_MODEL": "claude-opus-4-7",
        "ASU_AI_EMBEDDINGS_PROVIDER": "openai",
        "ASU_AI_EMBEDDINGS_MODEL": "te3s",
        "ASU_AI_EMBEDDINGS_DIMENSIONS": "1024",
        "JOB_CACHE_HOURS": "6",
        "CACHE_DIR": "./data/cache",
        "EMBEDDING_BATCH_WORKERS": "2",
        "PLAYWRIGHT_SKIP_BROWSER_INSTALL": "false",
    }
