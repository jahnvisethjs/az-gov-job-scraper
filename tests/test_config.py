"""Tests for deterministic environment configuration."""

import os

from config import _load_environment


def test_load_environment_reads_local_file(monkeypatch, tmp_path):
    variable = "JOB_SCRAPER_TEST_ENV"
    monkeypatch.delenv(variable, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"{variable}=from-dotenv\n", encoding="utf-8")

    assert _load_environment(env_file) is True
    assert os.environ[variable] == "from-dotenv"


def test_process_environment_takes_precedence(monkeypatch, tmp_path):
    variable = "JOB_SCRAPER_TEST_ENV"
    monkeypatch.setenv(variable, "from-process")
    env_file = tmp_path / ".env"
    env_file.write_text(f"{variable}=from-dotenv\n", encoding="utf-8")

    assert _load_environment(env_file) is True
    assert os.environ[variable] == "from-process"
